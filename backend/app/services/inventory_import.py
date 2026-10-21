"""
PNMP Inventory Import/Export Service (Milestone 1)

Excel bulk import of the network inventory workbook ("perangkat network.xlsx")
with preview-before-commit, per-row validation, duplicate detection (inside the
file and against the database), transactional commit with full rollback, and
per-row error reporting. CSV export reads actual database records only.

Data-integrity rules enforced here:
- Never invent management IPs, serial numbers, firmware versions, sites, or
  monitoring results. Missing optional fields stay NULL (unknown), never "N/A".
- The workbook contains NO credentials and this importer NEVER writes a
  DeviceCredential row. Credentials are configured separately through the
  existing secure credential mechanism.
- Imported devices are created with monitoring_enabled=False,
  monitoring_method=NONE and status=UNKNOWN: registration in the inventory is
  NOT proof of reachability; an operator must explicitly enable monitoring.
- Unresolved management addresses (e.g. the literal "ISP" in the IP Address
  column) are reported as INVALID rows and preserved for manual review — they
  are never silently dropped, merged, or converted to a fake address.
- Duplicate device names are allowed but flagged for review (the source
  workbook legitimately reuses names across buildings).
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import io
import ipaddress
import re
from typing import List, Optional

from sqlalchemy.orm import Session

from ..models import (
    Device,
    DeviceRole,
    DeviceStatus,
    MonitoringMethod,
    Site,
    User,
    UserRole,
)

# ---------------------------------------------------------------- constants

EXPECTED_COLUMNS = [
    "No", "Nama Perangkat", "Lokasi", "Fungsi", "Kondisi",
    "Merk", "Type", "Versi OS", "EOL/EOSL", "IP Address",
]

MAX_IMPORT_ROWS = 5000          # bounded input size (8 GB dev machine safety)
MAX_FIELD_LEN = 200             # any single normalized cell value

# Vendor normalization: lowercase alias -> canonical vendor name.
VENDOR_ALIASES = {
    "aruba": "Aruba", "hp aruba": "Aruba", "hpe aruba": "Aruba",
    "procurve": "Aruba", "alcatel-lucent enterprise": "Aruba", "aos-cx": "Aruba",
    "cisco": "Cisco", "cisco systems": "Cisco",
    "mikrotik": "MikroTik",
    "fortinet": "Fortinet", "fortigate": "Fortinet",
    "peplink": "Peplink",
}

# Keyword-based mapping of workbook Fungsi/Type text -> PNMP DeviceRole enum.
_ROLE_KEYWORDS = [
    (("wireless controller", "wlc", "mobility controller"), DeviceRole.WIRELESS_CONTROLLER),
    (("access point", "ap-", " ap ", "raps"), DeviceRole.ACCESS_POINT),
    (("clearpass", "radius", "controller nac", "nac"), DeviceRole.SERVER),
    (("firewall", "fortigate", "fortinet"), DeviceRole.FIREWALL),
    (("load balancer", "balance", "peplink"), DeviceRole.LOAD_BALANCER),
    (("core router", "cloud core", "router", "mikrotik"), DeviceRole.ROUTER),
    (("edge router", "border"), DeviceRole.ROUTER),
    (("core switch", "core"), DeviceRole.CORE_SWITCH),
    (("distribution", "dist", "distr"), DeviceRole.DISTRIBUTION_SWITCH),
    (("switch",), DeviceRole.ACCESS_SWITCH),
    (("server",), DeviceRole.SERVER),
]

_WS_RE = re.compile(r"\s+")


def _norm(value) -> str:
    """Whitespace-normalized string form of a cell value ('' when empty)."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return _WS_RE.sub(" ", str(value)).strip()


def normalize_vendor(raw: str) -> tuple[Optional[str], Optional[str]]:
    """Return (canonical_vendor, error). Unknown vendors pass through Title-Cased."""
    v = _norm(raw)
    if not v:
        return None, "Merk (vendor) is required"
    key = v.lower()
    if key in VENDOR_ALIASES:
        return VENDOR_ALIASES[key], None
    if len(v) <= 50:
        return v, None
    return None, f"Vendor name too long ({len(v)} chars)"


def map_device_role(*texts: str) -> str:
    """Map free-text Fungsi/Type to a PNMP DeviceRole value (never raises)."""
    joined = " " + " ".join(t.lower() for t in texts if t) + " "
    for keywords, role in _ROLE_KEYWORDS:
        if any(k in joined for k in keywords):
            return role.value
    return DeviceRole.OTHER.value


def classify_management_ip(raw: str) -> tuple[Optional[str], Optional[str]]:
    """Validate a management address.

    Returns (ip_or_None, error_or_None). A non-empty value that is neither a
    valid IPv4/IPv6 address nor a plausible hostname is an UNRESOLVED
    management address (e.g. the literal "ISP" used in the source workbook);
    it is reported as invalid so a human can resolve it. We never fabricate.
    """
    v = _norm(raw)
    if not v:
        return None, "IP Address is required"
    try:
        return str(ipaddress.ip_address(v)), None
    except ValueError:
        pass
    # A dotted numeric token that LOOKS like an IPv4 octet sequence but fails
    # ip_address() (e.g. "192.168.1300.999", "10.0.0") is malformed — reject it
    # instead of misclassifying it as a hostname.
    if re.fullmatch(r"(?:\d{1,3}\.){0,3}\d{1,3}", v):
        return None, f"Malformed IP address '{v}'"
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]{0,99}", v):
        return v, None  # hostname-style management address (kept verbatim)
    return None, (
        f"Unresolved management address '{v}': not a valid IP address or hostname"
    )


# ---------------------------------------------------------------- structures

@dataclass
class NormalizedRow:
    row_no: int                    # 1-based Excel row number (incl. header offset)
    src_no: str = ""               # original "No" column value
    name: str = ""
    location: str = ""
    function: str = ""
    condition: str = ""
    vendor_raw: str = ""
    model: str = ""
    os_version: str = ""
    eol_eosl: str = ""
    ip_raw: str = ""
    # validated output
    vendor: Optional[str] = None
    management_ip: Optional[str] = None
    device_type: str = ""
    device_role: str = DeviceRole.OTHER.value
    site_name: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duplicate_of_row: Optional[int] = None       # earlier file row with same IP
    duplicate_name_with_rows: List[int] = field(default_factory=list)
    db_existing_device_id: Optional[int] = None  # DB device with same IP/name

    def base_payload(self) -> dict:
        """Field values that would be written to the database (validated only)."""
        return {
            "hostname": self.name.lower().replace(" ", "-"),
            "display_name": self.name,
            "management_ip": self.management_ip,
            "vendor": self.vendor,
            "model": self.model or None,
            "device_type": self.device_type,
            "device_role": self.device_role,
            "location": self.location or None,
            "site_name": self.site_name,
            "description": self._description(),
            "firmware_version": self.os_version or None,
        }

    def _description(self) -> str:
        parts = []
        if self.function:
            parts.append(f"Fungsi: {self.function}")
        if self.condition:
            parts.append(f"Kondisi: {self.condition}")
        if self.eol_eosl:
            parts.append(f"EOL/EOSL: {self.eol_eosl}")
        return " | ".join(parts)


@dataclass
class ImportPreview:
    filename: str
    sheet: str
    total_rows: int
    valid_count: int
    invalid_count: int
    duplicate_in_file_count: int
    existing_in_db_count: int
    review_needed_count: int
    truncated: bool
    rows: List[NormalizedRow]

    def summary(self) -> dict:
        return {
            "filename": self.filename,
            "sheet": self.sheet,
            "total_rows": self.total_rows,
            "valid": self.valid_count,
            "invalid": self.invalid_count,
            "duplicate_in_file": self.duplicate_in_file_count,
            "existing_in_db": self.existing_in_db_count,
            "review_needed": self.review_needed_count,
            "truncated": self.truncated,
        }


@dataclass
class ImportResult:
    inserted: int
    skipped_duplicates: int
    invalid: int
    review_needed: int
    created_site_ids: List[int]
    imported_device_ids: List[int]
    message: str


# ---------------------------------------------------------------- parsing

def parse_workbook(content: bytes, filename: str = "") -> ImportPreview:
    """Parse xlsx bytes into a fully validated preview (no DB access yet)."""
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(content), data_only=True, read_only=True)
    ws = wb.active
    sheet_name = ws.title or "Sheet1"

    rows_iter = ws.iter_rows(values_only=True)
    header = [_norm(c) for c in (next(rows_iter, None) or [])]

    problems = []
    missing = [c for c in EXPECTED_COLUMNS if c not in header]
    extra = [c for c in header if c and c not in EXPECTED_COLUMNS]
    if missing:
        raise ValueError(
            "Workbook is missing required column(s): " + ", ".join(missing)
            + f" (found: {', '.join(h for h in header if h) or 'nothing'})"
        )
    if extra:
        problems.append("Unexpected column(s) ignored: " + ", ".join(extra))

    idx = {name: header.index(name) for name in EXPECTED_COLUMNS}

    raw_rows: List[NormalizedRow] = []
    truncated = False
    excel_row = 1  # header was row 1
    for values in rows_iter:
        excel_row += 1
        if values is None:
            continue
        cells = [_norm(values[i]) if i < len(values) else "" for i in idx.values()]
        if not any(cells):
            continue  # blank filler row — not a populated record
        if len(raw_rows) >= MAX_IMPORT_ROWS:
            truncated = True
            break
        src = dict(zip(EXPECTED_COLUMNS, cells))
        raw_rows.append(_to_normalized(excel_row, src))
    wb.close()

    # ---- per-row validation
    seen_names: dict[str, list[int]] = {}
    for r in raw_rows:
        if len(r.name) > MAX_FIELD_LEN or len(r.location) > MAX_FIELD_LEN:
            r.errors.append("Field exceeds maximum length")
        if not r.name:
            r.errors.append("Nama Perangkat (device name) is required")
        if not r.location:
            r.errors.append("Lokasi (site/location) is required")

        r.vendor, err = normalize_vendor(r.vendor_raw)
        if err:
            r.errors.append(f"Merk: {err}")

        r.device_type = r.model if r.model else "Unknown"
        r.device_role = map_device_role(r.function, r.model, r.vendor_raw)
        r.site_name = r.location or None

        ip, ip_err = classify_management_ip(r.ip_raw)
        if ip_err:
            r.errors.append(f"IP Address: {ip_err}")
        else:
            r.management_ip = ip

        if r.name:
            seen_names.setdefault(r.name.lower(), []).append(r.row_no)

    # ---- duplicates inside the file (same normalized IP)
    by_ip: dict[str, int] = {}
    for r in raw_rows:
        if not r.management_ip:
            continue
        key = r.management_ip.lower()
        if key in by_ip:
            r.duplicate_of_row = by_ip[key]
            r.warnings.append(
                f"Duplicate IP in file: same as row {by_ip[key]} — will be SKIPPED on import"
            )
        else:
            by_ip[key] = r.row_no

    # ---- repeated names (allowed, flagged)
    for low, rows in seen_names.items():
        if len(rows) > 1:
            for r in raw_rows:
                if r.name.lower() == low:
                    others = [x for x in rows if x != r.row_no]
                    r.duplicate_name_with_rows = others
                    r.warnings.append(
                        "Repeated device name in file (rows "
                        + ", ".join(str(x) for x in others)
                        + ") — allowed, flagged for manual review"
                    )

    # ---- conflicts against the database
    _annotate_db_conflicts(raw_rows)

    valid = [r for r in raw_rows if not r.errors]
    return ImportPreview(
        filename=filename or "(uploaded)",
        sheet=sheet_name,
        total_rows=len(raw_rows),
        valid_count=len(valid),
        invalid_count=sum(1 for r in raw_rows if r.errors),
        duplicate_in_file_count=sum(1 for r in raw_rows if r.duplicate_of_row),
        existing_in_db_count=sum(1 for r in raw_rows if r.db_existing_device_id),
        review_needed_count=sum(1 for r in raw_rows if r.warnings),
        truncated=truncated,
        rows=raw_rows,
    )


def _to_normalized(excel_row: int, src: dict) -> NormalizedRow:
    return NormalizedRow(
        row_no=excel_row,
        src_no=src["No"],
        name=src["Nama Perangkat"],
        location=src["Lokasi"],
        function=src["Fungsi"],
        condition=src["Kondisi"],
        vendor_raw=src["Merk"],
        model=src["Type"],
        os_version=src["Versi OS"],
        eol_eosl=src["EOL/EOSL"],
        ip_raw=src["IP Address"],
    )


def _annotate_db_conflicts(rows: List[NormalizedRow]) -> None:
    """Flag rows whose IP already exists in the device inventory."""
    from ..core.database import SessionLocal

    ips = sorted({r.management_ip for r in rows if r.management_ip})
    if not ips:
        return
    db = SessionLocal()
    try:
        placeholders = ips
        existing = (
            db.query(Device.id, Device.management_ip)
            .filter(Device.management_ip.in_(placeholders))
            .all()
        )
        by_ip = {ip: did for did, ip in existing}
        for r in rows:
            if r.management_ip and r.management_ip in by_ip:
                r.db_existing_device_id = by_ip[r.management_ip]
                r.warnings.append(
                    f"Management IP already registered on device id={by_ip[r.management_ip]} "
                    "— will be SKIPPED on import (no silent merge)"
                )
    finally:
        db.close()


# ---------------------------------------------------------------- commit

def commit_import(preview: ImportPreview) -> ImportResult:
    """Transactional import of the previewed rows.

    One SQLAlchemy session/transaction: either ALL insertable rows are written
    or nothing is (full rollback on any failure). Duplicates (in-file and
    already-in-DB) and invalid rows are skipped, never deleted or merged.
    """
    from ..core.database import SessionLocal

    db = SessionLocal()
    inserted = 0
    skipped_dupes = 0
    invalid = sum(1 for r in preview.rows if r.errors)
    review = sum(1 for r in preview.rows if r.warnings)
    created_sites: List[int] = []
    device_ids: List[int] = []
    try:
        site_cache: dict[str, Site] = {}
        for st in db.query(Site).all():
            site_cache[st.name.strip().lower()] = st

        for r in preview.rows:
            if r.errors:
                continue
            if r.duplicate_of_row or r.db_existing_device_id:
                skipped_dupes += 1
                continue

            site = None
            if r.site_name:
                key = r.site_name.lower()
                site = site_cache.get(key)
                if site is None:
                    site = Site(name=r.site_name[:100])
                    db.add(site)
                    db.flush()  # obtain site.id inside the same transaction
                    site_cache[key] = site
                    created_sites.append(site.id)

            payload = r.base_payload()
            device = Device(
                hostname=payload["hostname"][:100],
                display_name=payload["display_name"][:150],
                management_ip=payload["management_ip"][:45],
                vendor=payload["vendor"][:50],
                model=payload["model"],
                device_type=payload["device_type"][:50],
                device_role=DeviceRole(payload["device_role"]),
                site_id=site.id if site else None,
                location=payload["location"][:200] if payload["location"] else None,
                description=payload["description"],
                firmware_version=payload["firmware_version"][:50] if payload["firmware_version"] else None,
                # Honest defaults — registration is not proof of reachability:
                status=DeviceStatus.UNKNOWN,
                monitoring_enabled=False,
                monitoring_method=MonitoringMethod.NONE,
                is_demo=False,
            )
            db.add(device)
            db.flush()
            device_ids.append(device.id)
            inserted += 1

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return ImportResult(
        inserted=inserted,
        skipped_duplicates=skipped_dupes,
        invalid=invalid,
        review_needed=review,
        created_site_ids=created_sites,
        imported_device_ids=device_ids,
        message=(
            f"Imported {inserted} device(s); skipped {skipped_dupes} duplicate(s); "
            f"{invalid} invalid row(s) require correction; {review} row(s) flagged for review."
        ),
    )


# ---------------------------------------------------------------- audit + RBAC

def write_audit(db: Session, user_id: Optional[int], action: str,
                resource: str, resource_id: Optional[str], details: str,
                ip_address: Optional[str] = None) -> None:
    from ..models import AuditLog

    db.add(AuditLog(user_id=user_id, action=action, resource=resource,
                    resource_id=resource_id, details=details, ip_address=ip_address))
    db.commit()


def assert_inventory_writer(user) -> None:
    """RBAC gate for inventory mutations (import) — mirrors users.py style."""
    if user.role not in (UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.NETWORK_ENGINEER):
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: inventory import requires Admin or Network Engineer role",
        )


def assert_report_reader(user) -> None:
    """RBAC gate for exports (any authenticated role may read inventory)."""
    return None


# ---------------------------------------------------------------- CSV export

_EXPORT_HEADERS = [
    "id", "hostname", "display_name", "management_ip", "vendor", "model",
    "device_type", "device_role", "site", "location", "status",
    "monitoring_enabled", "firmware_version", "last_seen", "notes",
]


def devices_to_csv(db: Session) -> str:
    """Serialize ACTUAL database records to CSV. No fabricated values."""
    import csv

    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")
    writer.writerow(_EXPORT_HEADERS)
    rows = (
        db.query(Device, Site.name)
        .outerjoin(Site, Device.site_id == Site.id)
        .order_by(Device.id)
        .all()
    )
    for device, site_name in rows:
        writer.writerow([
            device.id, device.hostname, device.display_name, device.management_ip,
            device.vendor, device.model or "", device.device_type,
            device.device_role.value if device.device_role else "",
            site_name or "", device.location or "",
            device.status.value if device.status else "unknown",
            "yes" if device.monitoring_enabled else "no",
            device.firmware_version or "",
            device.last_seen.isoformat() if device.last_seen else "",
            (device.description or "").replace("\n", " "),
        ])
    return out.getvalue()
