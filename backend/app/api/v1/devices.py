"""
PNMP Devices API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, Form, UploadFile, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import asyncio
import ipaddress
import json
import os
import re
import subprocess
import time

from ...core.database import get_db
from ...core.deps import get_current_user
from ...core.encryption import credential_encryption
from ...models import User, Device, DeviceCredential, Site, DeviceStatus, MonitoringMethod
from ...schemas import (
    DeviceCreate, DeviceUpdate, DeviceResponse,
    DeviceCredentialCreate, DeviceCredentialSafeResponse, TestConnectionResponse
)

router = APIRouter(prefix="/devices", tags=["Devices"])

# PHASE 3 / MILESTONE 1: inventory mutations (create/update/delete/import) are
# restricted server-side to Admin/Engineer roles. Read-only users (viewer/operator)
# keep full read access. This mirrors the existing pattern in users.py and cannot
# be bypassed by hiding UI controls.
from ...services import inventory_import as inv
from ...models import UserRole, AuditLog

_INVENTORY_WRITE_ROLES = (UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.NETWORK_ENGINEER)
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB workbook cap (bounded memory on dev machine)


def _require_inventory_writer(user: User) -> None:
    if user.role not in _INVENTORY_WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: device inventory changes require Admin or Network Engineer role",
        )


def _preview_to_dict(pv) -> dict:
    return {
        "summary": pv.summary(),
        "rows": [
            {
                "row_no": r.row_no,
                "src_no": r.src_no,
                "name": r.name,
                "location": r.location,
                "function": r.function,
                "condition": r.condition,
                "vendor_raw": r.vendor_raw,
                "vendor": r.vendor,
                "model": r.model,
                "os_version": r.os_version,
                "eol_eosl": r.eol_eosl,
                "ip_raw": r.ip_raw,
                "management_ip": r.management_ip,
                "device_type": r.device_type,
                "device_role": r.device_role,
                "errors": r.errors,
                "warnings": r.warnings,
                "duplicate_of_row": r.duplicate_of_row,
                "db_existing_device_id": r.db_existing_device_id,
                "site_id": r.site_id,
                "site_status": r.site_status,
                "status": "invalid" if r.errors else ("skip_duplicate" if (r.duplicate_of_row or r.db_existing_device_id) else ("skip_site_review" if (r.site_status in ("new_pending_approval", "ambiguous") and not r.duplicate_of_row and not r.db_existing_device_id) else "importable")),
            }
            for r in pv.rows
        ],
        "site_mapping": [
            {
                "location": e.location,
                "status": e.status,
                "site_id": e.site_id,
                "site_name": e.site_name,
                "candidates": e.candidates,
                "row_numbers": e.row_numbers,
            }
            for e in pv.site_mapping
        ],
    }


# PHASE 3 STEP 8 (async API safety): helpers for the connection test.
# - strict allow-list validation of the stored management IP prevents any
#   shell-command injection vector (no user-supplied commands are ever run)
# - ping runs in a bounded worker thread via asyncio.to_thread so the FastAPI
#   event loop stays responsive during polling/tests
# - hard timeout enforced on top of the OS-level ping timeout

_HOSTNAME_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9\-\.]{0,251}[A-Za-z0-9])?$")


def _is_valid_host(value: str) -> bool:
    """Strictly validate an IPv4/IPv6 address or hostname before use as a ping target."""
    if not value or len(value) > 253:
        return False
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        pass
    return bool(_HOSTNAME_RE.match(value)) and ".." not in value


async def _ping_async(target: str, timeout_seconds: int = 5) -> bool:
    """Run one ICMP ping echo without blocking the event loop.

    The argument list is fixed ('ping', '-n'/'-c', '1', '-w', ms, target);
    no shell is used and the target is pre-validated by the caller.
    """
    if os.name == "nt":
        cmd = ["ping", "-n", "1", "-w", str(timeout_seconds * 1000), target]
    else:
        cmd = ["ping", "-c", "1", "-W", str(timeout_seconds), target]

    def _run():
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout_seconds + 2
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, OSError):
            return False

    return await asyncio.to_thread(_run)


def _device_to_response(device: Device, db: Session) -> dict:
    """Convert Device model to response dict with site name"""
    site = db.query(Site).filter(Site.id == device.site_id).first() if device.site_id else None
    return {
        "id": device.id,
        "hostname": device.hostname,
        "display_name": device.display_name,
        "management_ip": device.management_ip,
        "vendor": device.vendor,
        "model": device.model,
        "serial_number": device.serial_number,
        "device_type": device.device_type,
        "device_role": device.device_role,
        "site_id": device.site_id,
        "site_name": site.name if site else None,
        "location": device.location,
        "status": device.status,
        "monitoring_enabled": device.monitoring_enabled,
        "monitoring_method": device.monitoring_method,
        "polling_interval_seconds": device.polling_interval_seconds,
        "description": device.description,
        "firmware_version": device.firmware_version,
        "mac_address": device.mac_address,
        "uptime": device.uptime,
        "cpu_usage": device.cpu_usage,
        "memory_usage": device.memory_usage,
        "temperature": device.temperature,
        "last_seen": device.last_seen,
        "failure_count": device.failure_count,
        "created_at": device.created_at,
        "updated_at": device.updated_at
    }


@router.get("/", response_model=List[DeviceResponse])
async def get_devices(
    skip: int = 0,
    limit: int = 100,
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    site_id: Optional[int] = None,
    vendor: Optional[str] = None,
    device_type: Optional[str] = None,
    device_role: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    monitoring_enabled: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all devices with optional filters and pagination"""
    query = db.query(Device)
    
    # Apply filters
    if site_id:
        query = query.filter(Device.site_id == site_id)
    if vendor:
        query = query.filter(Device.vendor.ilike(f"%{vendor}%"))
    if device_type:
        query = query.filter(Device.device_type.ilike(f"%{device_type}%"))
    if device_role:
        query = query.filter(Device.device_role == device_role)
    if status_filter:
        query = query.filter(Device.status == status_filter)
    if monitoring_enabled is not None:
        query = query.filter(Device.monitoring_enabled == monitoring_enabled)
    if search:
        query = query.filter(
            (Device.display_name.ilike(f"%{search}%")) |
            (Device.hostname.ilike(f"%{search}%")) |
            (Device.management_ip.ilike(f"%{search}%"))
        )
    
    # Pagination
    if page and page_size:
        total = query.count()
        offset = (page - 1) * page_size
        devices = query.offset(offset).limit(page_size).all()
    else:
        devices = query.offset(skip).limit(limit).all()
    
    return [_device_to_response(d, db) for d in devices]


@router.post("/import/preview")
async def import_preview(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preview an Excel inventory import WITHOUT writing anything to the database.

    Validates columns and values, normalizes whitespace, validates management
    addresses, maps vendor/device role, detects duplicates inside the file and
    against existing records, and reports per-row errors/warnings. Nothing is
    committed at this stage (requirement: preview before commit).
    """
    _require_inventory_writer(current_user)
    name = os.path.basename(file.filename or "")
    if not name.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx workbooks are supported")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Workbook exceeds the 5 MB upload limit")
    try:
        pv = inv.parse_workbook(content, filename=name, db=db)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        # never leak parser internals/paths
        raise HTTPException(status_code=422, detail="Unable to read workbook (invalid or corrupt xlsx)")
    return {"success": True, "mode": "preview", **_preview_to_dict(pv)}


@router.post("/import")
async def import_commit(
    request: Request,
    file: UploadFile = File(...),
    approved_sites: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transactional bulk import of an Excel workbook into the device inventory.

    The workbook is re-validated server-side (the preview token cannot be used
    to smuggle unvalidated rows). Either all insertable rows commit or nothing
    does (full rollback). Duplicate and invalid rows are SKIPPED — never
    silently deleted or merged. No credentials are imported; devices start with
    monitoring disabled and status UNKNOWN (registration != reachability).

    Site policy: locations that do not match an existing site are skipped
    UNLESS their exact workbook value appears in ``approved_sites`` (comma-
    separated list reviewed by the operator in the preview). Ambiguous
    locations are always skipped for manual resolution. Every attempt is
    written to the audit log.
    """
    _require_inventory_writer(current_user)
    name = os.path.basename(file.filename or "")
    if not name.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx workbooks are supported")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Workbook exceeds the 5 MB upload limit")
    try:
        pv = inv.parse_workbook(content, filename=name, db=db)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        raise HTTPException(status_code=422, detail="Unable to read workbook (invalid or corrupt xlsx)")

    dry_run = request.query_params.get("dry_run", "").lower() in ("1", "true", "yes")
    if dry_run:
        return {"success": True, "mode": "dry_run", **_preview_to_dict(pv)}

    approved = [s.strip() for s in (approved_sites or "").split(",") if s.strip()]

    # commit_import opens its OWN session/transaction (full rollback on any
    # failure); it never reuses the request session for writes.
    try:
        result = inv.commit_import(pv, approved_sites=approved)
    except Exception:
        db.add(AuditLog(user_id=current_user.id, action="device_import_failed",
                        resource="devices", resource_id=None,
                        details=f"Import of '{name}' rolled back entirely (transactional)",
                        ip_address=request.client.host if request.client else None))
        db.commit()
        raise HTTPException(status_code=500, detail="Import failed; the transaction was rolled back and no rows were written")

    db.add(AuditLog(user_id=current_user.id, action="device_import",
                    resource="devices", resource_id=None,
                    details=(f"file={name}; inserted={result.inserted}; "
                             f"skipped_duplicates={result.skipped_duplicates}; invalid={result.invalid}; "
                             f"skipped_site_review={result.skipped_site_review}; "
                             f"approved_sites={len(approved)}"),
                    ip_address=request.client.host if request.client else None))
    db.commit()

    return {
        "success": True,
        "mode": "committed",
        "summary": {**pv.summary(),
                    "inserted": result.inserted,
                    "skipped": result.skipped_duplicates,
                    "skipped_site_review": result.skipped_site_review,
                    "created_sites": len(result.created_site_ids)},
        "message": result.message,
        "imported_device_ids": result.imported_device_ids,
    }


@router.get("/export.csv")
async def export_devices_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export the ACTUAL device inventory as CSV (any authenticated role may read)."""
    from fastapi.responses import StreamingResponse

    csv_text = inv.devices_to_csv(db)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"pnmp_device_inventory_{stamp}.csv"
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new device (Admin/Engineer only — server-side RBAC)"""
    _require_inventory_writer(current_user)
    # Verify site exists if provided
    if device_data.site_id:
        site = db.query(Site).filter(Site.id == device_data.site_id).first()
        if not site:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Site not found"
            )
    
    # Create device
    db_device = Device(
        hostname=device_data.hostname,
        display_name=device_data.display_name,
        management_ip=device_data.management_ip,
        vendor=device_data.vendor,
        model=device_data.model,
        serial_number=device_data.serial_number,
        device_type=device_data.device_type,
        device_role=device_data.device_role,
        site_id=device_data.site_id,
        location=device_data.location,
        description=device_data.description,
        monitoring_enabled=device_data.monitoring_enabled,
        monitoring_method=device_data.monitoring_method,
        polling_interval_seconds=device_data.polling_interval_seconds,
        firmware_version=device_data.firmware_version,
        mac_address=device_data.mac_address,
        status=DeviceStatus.UNKNOWN
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    
    return _device_to_response(db_device, db)


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get device by ID"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return _device_to_response(device, db)


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update device (Admin/Engineer only — server-side RBAC)"""
    _require_inventory_writer(current_user)
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # MILESTONE 1 (data integrity): management_ip is the address monitoring and
    # connection tests probe. Changing it must NOT carry over reachability
    # evidence collected for the OLD address — reset observed state so the
    # device honestly returns to UNKNOWN until re-probed.
    ip_changed = (
        device_data.management_ip is not None
        and device_data.management_ip != device.management_ip
    )

    # Update fields
    update_data = device_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(device, key, value)

    if ip_changed:
        device.status = DeviceStatus.UNKNOWN
        device.failure_count = 0
        device.last_seen = None
    
    db.commit()
    db.refresh(device)
    
    return _device_to_response(device, db)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete device (Admin/Engineer only — server-side RBAC; UI asks confirmation)"""
    _require_inventory_writer(current_user)
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    db.delete(device)
    db.commit()


@router.post("/{device_id}/test-connection", response_model=TestConnectionResponse)
async def test_connection(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test connectivity to device (ping + method-specific test)"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Step 1: Basic ping test
    # PHASE 3 STEP 8: non-blocking (asyncio.to_thread), strict target validation
    # (no injection vector; fixed argv, no shell), hard timeout, sanitized errors.
    if not _is_valid_host(device.management_ip):
        return TestConnectionResponse(
            success=False,
            device_id=device_id,
            method="ICMP",
            latency_ms=None,
            message="Device management address is not a valid IP/hostname",
            error_code="INVALID_TARGET"
        )

    start_time = time.time()
    try:
        reachable = await _ping_async(device.management_ip, timeout_seconds=5)
        latency = (time.time() - start_time) * 1000

        if reachable:
            # Update last_seen
            device.last_seen = datetime.utcnow()
            device.failure_count = 0
            if device.status == DeviceStatus.DOWN:
                device.status = DeviceStatus.UP
            db.commit()

            return TestConnectionResponse(
                success=True,
                device_id=device_id,
                method="ICMP",
                latency_ms=round(latency, 2),
                message=f"Device {device.management_ip} is reachable"
            )
        else:
            # Increment failure count
            device.failure_count = (device.failure_count or 0) + 1
            db.commit()

            return TestConnectionResponse(
                success=False,
                device_id=device_id,
                method="ICMP",
                latency_ms=None,
                message=f"Device {device.management_ip} is not reachable",
                error_code="ICMP_UNREACHABLE"
            )
    except Exception:
        # PHASE 3 STEP 8: never leak exception details (paths, commands, internals)
        db.rollback()
        return TestConnectionResponse(
            success=False,
            device_id=device_id,
            method="ICMP",
            latency_ms=None,
            message="Connection test failed",
            error_code="TEST_ERROR"
        )


@router.post("/{device_id}/credentials", response_model=DeviceCredentialSafeResponse)
async def set_credentials(
    device_id: int,
    cred_data: DeviceCredentialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Set device credentials (encrypted).
    All secrets are encrypted before storage.
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Delete existing credentials for this device
    db.query(DeviceCredential).filter(DeviceCredential.device_id == device_id).delete()
    
    # Create new credentials with encryption
    db_cred = DeviceCredential(
        device_id=device_id,
        username=cred_data.username,
        encrypted_password=credential_encryption.encrypt(cred_data.password) if cred_data.password else None,
        snmp_version=cred_data.snmp_version,
        snmp_community_encrypted=credential_encryption.encrypt(cred_data.snmp_community) if cred_data.snmp_community else None,
        snmp_username=cred_data.snmp_username,
        snmp_auth_protocol=cred_data.snmp_auth_protocol,
        snmp_auth_password_encrypted=credential_encryption.encrypt(cred_data.snmp_auth_password) if cred_data.snmp_auth_password else None,
        snmp_privacy_protocol=cred_data.snmp_privacy_protocol,
        snmp_privacy_password_encrypted=credential_encryption.encrypt(cred_data.snmp_privacy_password) if cred_data.snmp_privacy_password else None,
        ssh_enabled=cred_data.ssh_enabled,
        api_enabled=cred_data.api_enabled,
        snmp_enabled=cred_data.snmp_enabled
    )
    db.add(db_cred)
    db.commit()
    db.refresh(db_cred)
    
    # Return SAFE response (no secrets)
    return DeviceCredentialSafeResponse(
        device_id=device_id,
        username_configured=bool(cred_data.username),
        password_configured=bool(cred_data.password),
        snmp_configured=bool(cred_data.snmp_community or cred_data.snmp_username),
        snmp_version=cred_data.snmp_version,
        snmp_v3_configured=bool(cred_data.snmp_username),
        ssh_enabled=cred_data.ssh_enabled,
        api_enabled=cred_data.api_enabled,
        snmp_enabled=cred_data.snmp_enabled,
        created_at=db_cred.created_at,
        updated_at=db_cred.updated_at
    )


@router.get("/{device_id}/credentials", response_model=DeviceCredentialSafeResponse)
async def get_credentials(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get device credential STATUS (safe response).
    NEVER returns actual passwords or secrets.
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    cred = db.query(DeviceCredential).filter(DeviceCredential.device_id == device_id).first()
    if not cred:
        return DeviceCredentialSafeResponse(
            device_id=device_id,
            username_configured=False,
            password_configured=False,
            snmp_configured=False,
            snmp_version=None,
            snmp_v3_configured=False,
            ssh_enabled=False,
            api_enabled=False,
            snmp_enabled=True
        )
    
    return DeviceCredentialSafeResponse(
        device_id=device_id,
        username_configured=bool(cred.username),
        password_configured=bool(cred.encrypted_password),
        snmp_configured=bool(cred.snmp_community_encrypted or cred.snmp_username),
        snmp_version=cred.snmp_version,
        snmp_v3_configured=bool(cred.snmp_username),
        ssh_enabled=cred.ssh_enabled,
        api_enabled=cred.api_enabled,
        snmp_enabled=cred.snmp_enabled,
        created_at=cred.created_at,
        updated_at=cred.updated_at
    )


# ==================== INTERFACE ENDPOINTS ====================

@router.get("/{device_id}/interfaces", response_model=List[dict])
async def get_device_interfaces(
    device_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all interfaces for a device"""
    from ...models import DeviceInterface
    
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    query = db.query(DeviceInterface).filter(DeviceInterface.device_id == device_id)
    
    if status_filter:
        query = query.filter(DeviceInterface.status == status_filter)
    if search:
        query = query.filter(
            (DeviceInterface.name.ilike(f"%{search}%")) |
            (DeviceInterface.description.ilike(f"%{search}%"))
        )
    
    interfaces = query.all()
    
    return [
        {
            "id": iface.id,
            "device_id": iface.device_id,
            "if_index": iface.if_index,
            "name": iface.name,
            "description": iface.description,
            "alias": iface.alias,
            "status": iface.status,
            "admin_status": iface.admin_status,
            "speed": iface.speed,
            "speed_bps": iface.speed_bps,
            "duplex": iface.duplex,
            "rx_bytes": iface.rx_bytes,
            "tx_bytes": iface.tx_bytes,
            "rx_errors": iface.rx_errors,
            "tx_errors": iface.tx_errors,
            "rx_discards": iface.rx_discards,
            "tx_discards": iface.tx_discards,
            "rx_bps": iface.rx_bps,
            "tx_bps": iface.tx_bps,
            "utilization": iface.utilization,
            "utilization_in": iface.utilization_in,
            "utilization_out": iface.utilization_out,
            "last_polled": iface.last_polled
        }
        for iface in interfaces
    ]
