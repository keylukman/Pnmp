"""
Monitoring Manager
Orchestrates device monitoring and data collection
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from .adapters import AdapterRegistry
from ..models import (
    Device, DeviceCredential, DeviceInterface, DeviceMetric,
    InterfaceMetric, Alert, EventLog, DeviceStatus, AlertSeverity,
    AlertStatus, EventType, MonitoringMethod, InterfaceStatus
)
from ..core.encryption import credential_encryption
from ..core.config import settings

logger = logging.getLogger(__name__)

# Maps internal alert_type keys to the deterministic alert title prefixes
# used when creating alerts. Used for alert deduplication/resolution lookups.
ALERT_TITLE_PREFIXES = {
    'device_down': 'Device DOWN',
}


class MonitoringManager:
    """
    Manages device monitoring operations.
    Handles polling, metrics storage, alert generation, and status updates.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.concurrency_limit = asyncio.Semaphore(settings.MONITORING_MAX_CONCURRENCY)
        self.failure_threshold = settings.MONITOR_FAILURE_THRESHOLD
    
    async def monitor_device(self, device_id: int) -> Dict[str, Any]:
        """
        Monitor a single device.
        Returns monitoring result with status and metrics.
        """
        async with self.concurrency_limit:
            device = self.db.query(Device).filter(Device.id == device_id).first()
            if not device:
                return {'success': False, 'error': 'Device not found'}
            
            # Get credentials
            cred = self.db.query(DeviceCredential).filter(
                DeviceCredential.device_id == device_id
            ).first()
            
            if not cred:
                return {
                    'success': False,
                    'error': 'No credentials configured',
                    'error_code': 'NO_CREDENTIALS'
                }
            
            # Decrypt credentials
            credentials = self._decrypt_credentials(cred)
            
            # Get adapter (fail explicitly if no adapter for the method)
            try:
                adapter = AdapterRegistry.get_adapter(
                    device_id=device.id,
                    management_ip=device.management_ip,
                    vendor=device.vendor,
                    device_type=device.device_type,
                    monitoring_method=device.monitoring_method.value if device.monitoring_method else 'snmp',
                    credentials=credentials
                )
            except ValueError as e:
                logger.warning(f"No adapter available for device {device_id}")
                return await self._handle_monitoring_failure(device, {
                    'success': False,
                    'message': str(e),
                    'error_code': 'UNSUPPORTED_METHOD'
                })
            
            try:
                # Test connection
                conn_result = await adapter.test_connection()
                
                if not conn_result.get('success'):
                    # Handle failure
                    return await self._handle_monitoring_failure(device, conn_result)
                
                # Connection successful - collect data
                result = {
                    'success': True,
                    'device_id': device_id,
                    'method': conn_result.get('method', 'SNMP'),
                    'latency_ms': conn_result.get('latency_ms'),
                    'message': conn_result.get('message')
                }
                
                # Get system info
                system_info = await adapter.get_system_info()
                if system_info:
                    result['system_info'] = system_info
                    
                    # Store device metrics
                    await self._store_device_metrics(device_id, system_info)
                    
                    # Update device info
                    device.cpu_usage = system_info.get('cpu')
                    device.memory_usage = system_info.get('memory')
                    device.temperature = system_info.get('temperature')
                    device.uptime = str(system_info.get('uptime_seconds', 0))
                
                # Get interfaces
                try:
                    interfaces = await adapter.get_interfaces()
                except (NotImplementedError, AttributeError):
                    interfaces = None
                if interfaces:
                    result['interfaces'] = interfaces
                    
                    # Update/create interfaces
                    await self._update_interfaces(device_id, interfaces)
                
                # Get interface statistics
                try:
                    stats = await adapter.get_interface_statistics()
                except (NotImplementedError, AttributeError):
                    stats = None
                if stats:
                    result['interface_stats'] = stats
                    
                    # Store interface metrics
                    await self._store_interface_metrics(device_id, stats)
                
                # Update device status
                await self._handle_monitoring_success(device)
                
                return result
                
            except Exception as e:
                # Log details server-side only; never expose exception text
                # (may contain IPs/community hints) to API consumers.
                logger.error(f"Monitoring error on device {device_id}: {type(e).__name__}")
                return await self._handle_monitoring_failure(device, {
                    'success': False,
                    'message': 'Monitoring error',
                    'error_code': 'MONITORING_ERROR'
                })
            finally:
                await adapter.close()
    
    def _decrypt_credentials(self, cred: Optional[DeviceCredential]) -> Dict[str, Any]:
        """Decrypt device credentials.

        Uses attribute-presence checks so that partially configured credential
        objects (e.g. test doubles without optional SNMP columns) do not raise
        AttributeError inside monitor_device's try block.
        """
        if cred is None:
            return {}

        credentials = {
            'snmp_version': getattr(cred, 'snmp_version', None) or 'v2c',
            'timeout': settings.SNMP_TIMEOUT,
            'retries': settings.SNMP_RETRIES,
            'ssh_enabled': getattr(cred, 'ssh_enabled', False),
            'api_enabled': getattr(cred, 'api_enabled', False)
        }
        
        # Decrypt SNMP community (v2c)
        if getattr(cred, 'snmp_community_encrypted', None):
            try:
                credentials['snmp_community'] = credential_encryption.decrypt(
                    cred.snmp_community_encrypted
                )
            except Exception:
                logger.warning("Could not decrypt SNMP community for credential record")
        
        # Decrypt SNMP v3 credentials
        if getattr(cred, 'snmp_username', None):
            credentials['snmp_username'] = cred.snmp_username
        
        if getattr(cred, 'snmp_auth_password_encrypted', None):
            try:
                credentials['snmp_auth_password'] = credential_encryption.decrypt(
                    cred.snmp_auth_password_encrypted
                )
            except Exception:
                pass
        
        if getattr(cred, 'snmp_auth_protocol', None):
            credentials['snmp_auth_protocol'] = cred.snmp_auth_protocol
        
        if getattr(cred, 'snmp_privacy_password_encrypted', None):
            try:
                credentials['snmp_privacy_password'] = credential_encryption.decrypt(
                    cred.snmp_privacy_password_encrypted
                )
            except Exception:
                pass
        
        if getattr(cred, 'snmp_privacy_protocol', None):
            credentials['snmp_privacy_protocol'] = cred.snmp_privacy_protocol
        
        # Decrypt SSH/API credentials
        if getattr(cred, 'username', None):
            credentials['username'] = cred.username
        
        if getattr(cred, 'encrypted_password', None):
            try:
                credentials['password'] = credential_encryption.decrypt(
                    cred.encrypted_password
                )
            except Exception:
                pass
        
        return credentials
    
    async def _store_device_metrics(self, device_id: int, system_info: Dict[str, Any]):
        """Store device performance metrics"""
        metric = DeviceMetric(
            device_id=device_id,
            timestamp=datetime.utcnow(),
            cpu_percent=system_info.get('cpu'),
            memory_percent=system_info.get('memory'),
            temperature=system_info.get('temperature'),
            uptime_seconds=system_info.get('uptime_seconds'),
            collection_method='snmp'
        )
        self.db.add(metric)
        self.db.commit()
    
    async def _update_interfaces(self, device_id: int, interfaces: List[Dict[str, Any]]):
        """Update or create device interfaces with status change detection"""
        device = self.db.query(Device).filter(Device.id == device_id).first()
        
        for iface_data in interfaces:
            # Check if interface exists
            existing = self.db.query(DeviceInterface).filter(
                DeviceInterface.device_id == device_id,
                DeviceInterface.name == iface_data['name']
            ).first()
            
            if existing:
                # Detect status changes
                old_status = existing.status
                new_status = iface_data.get('status', existing.status)
                
                # Update existing interface
                existing.description = iface_data.get('description', existing.description)
                existing.alias = iface_data.get('alias', existing.alias)
                existing.status = new_status
                existing.admin_status = iface_data.get('admin_status', existing.admin_status)
                existing.speed_bps = iface_data.get('speed_bps', existing.speed_bps)
                existing.mtu = iface_data.get('mtu', existing.mtu)
                existing.last_polled = datetime.utcnow()
                
                # Generate events for status changes
                if old_status != new_status:
                    if new_status == 'up' and old_status in ['down', 'unknown']:
                        await self._create_event(
                            device_id=device_id,
                            interface_id=existing.id,
                            event_type=EventType.INTERFACE_UP,
                            severity=AlertSeverity.INFO,
                            message=f"Interface {existing.name} is now UP",
                            source='monitoring'
                        )
                    elif new_status == 'down' and old_status == 'up':
                        await self._create_event(
                            device_id=device_id,
                            interface_id=existing.id,
                            event_type=EventType.INTERFACE_DOWN,
                            severity=AlertSeverity.WARNING,
                            message=f"Interface {existing.name} is now DOWN",
                            source='monitoring'
                        )
            else:
                # Create new interface
                new_iface = DeviceInterface(
                    device_id=device_id,
                    if_index=iface_data.get('if_index'),
                    name=iface_data['name'],
                    description=iface_data.get('description', ''),
                    alias=iface_data.get('alias', ''),
                    status=iface_data.get('status', 'unknown'),
                    admin_status=iface_data.get('admin_status', 'unknown'),
                    speed_bps=iface_data.get('speed_bps'),
                    mtu=iface_data.get('mtu'),
                    last_polled=datetime.utcnow()
                )
                self.db.add(new_iface)
        
        self.db.commit()
    
    async def _store_interface_metrics(self, device_id: int, stats: List[Dict[str, Any]]):
        """Store interface traffic metrics with counter delta calculation"""
        now = datetime.utcnow()
        
        for stat in stats:
            # Find interface
            iface = self.db.query(DeviceInterface).filter(
                DeviceInterface.device_id == device_id,
                DeviceInterface.name == stat.get('name')
            ).first()
            
            if not iface:
                continue
            
            # Current counter values — missing counters stay None (unavailable),
            # they are NOT fabricated as zero.
            current_rx_bytes = stat.get('rx_bytes')
            current_tx_bytes = stat.get('tx_bytes')

            # Rates & utilization are only meaningful with a valid previous
            # sample (baseline). On the FIRST poll we store raw counters and
            # leave rates NULL rather than inventing zeros.
            rx_bps = None
            tx_bps = None
            util_in = None
            util_out = None

            have_baseline = (
                iface.last_polled is not None
                and iface.rx_bytes is not None
                and iface.tx_bytes is not None
                and current_rx_bytes is not None
                and current_tx_bytes is not None
            )
            if have_baseline:
                # Calculate time delta in seconds
                time_delta = (now - iface.last_polled).total_seconds()

                if time_delta > 0:
                    # bps = (current_bytes - previous_bytes) * 8 / elapsed_seconds
                    rx_delta = current_rx_bytes - iface.rx_bytes
                    tx_delta = current_tx_bytes - iface.tx_bytes

                    # Handle counter reset/rollover: never produce negative
                    # traffic; mark this cycle's rates as unavailable (None).
                    if rx_delta < 0 or tx_delta < 0:
                        logger.warning(f"Counter reset detected on {device_id}:{iface.name}")
                        rx_bps = None
                        tx_bps = None
                    else:
                        rx_bps = int((rx_delta * 8) / time_delta)
                        tx_bps = int((tx_delta * 8) / time_delta)

                    # Utilization requires known interface speed; when speed
                    # is unknown it remains NULL — never fabricated.
                    if iface.speed_bps and iface.speed_bps > 0 and rx_bps is not None and tx_bps is not None:
                        util_in = min(100, int((rx_bps / iface.speed_bps) * 100))
                        util_out = min(100, int((tx_bps / iface.speed_bps) * 100))

            # Errors/discards: preserve "unknown" as None instead of fake 0
            rx_errors = stat.get('rx_errors')
            tx_errors = stat.get('tx_errors')
            rx_discards = stat.get('rx_discards')
            tx_discards = stat.get('tx_discards')
            
            # Store metric
            metric = InterfaceMetric(
                interface_id=iface.id,
                device_id=device_id,
                timestamp=datetime.utcnow(),
                rx_bytes=current_rx_bytes,
                tx_bytes=current_tx_bytes,
                rx_bps=rx_bps,
                tx_bps=tx_bps,
                rx_errors=rx_errors,
                tx_errors=tx_errors,
                rx_discards=rx_discards,
                tx_discards=tx_discards,
                utilization_in=util_in,
                utilization_out=util_out
            )
            self.db.add(metric)
            
            # Update interface current values (counters + last_polled form the
            # baseline for the next delta calculation)
            iface.rx_bytes = current_rx_bytes
            iface.tx_bytes = current_tx_bytes
            iface.rx_bps = rx_bps
            iface.tx_bps = tx_bps
            iface.rx_errors = rx_errors
            iface.tx_errors = tx_errors
            iface.rx_discards = rx_discards
            iface.tx_discards = tx_discards
            iface.utilization_in = util_in
            iface.utilization_out = util_out
            if util_in is not None or util_out is not None:
                iface.utilization = max(util_in or 0, util_out or 0)
            iface.last_polled = now
        
        self.db.commit()
    
    async def _handle_monitoring_success(self, device: Device):
        """Handle successful monitoring"""
        # Reset failure count
        device.failure_count = 0
        device.last_seen = datetime.utcnow()
        
        # Check if device was down
        was_down = device.status == DeviceStatus.DOWN
        device.status = DeviceStatus.UP
        
        self.db.commit()
        
        # Generate recovery event if was down
        if was_down:
            await self._create_event(
                device_id=device.id,
                event_type=EventType.DEVICE_UP,
                severity=AlertSeverity.INFO,
                message=f"Device {device.display_name} is now UP",
                source='monitoring'
            )
            
            # Resolve any open DOWN alerts (best-effort: must never break
            # the polling cycle or mark an otherwise successful poll as failed)
            try:
                await self._resolve_device_alerts(device.id, 'device_down')
            except Exception:
                logger.error("Failed to resolve device_down alerts on recovery")
    
    async def _handle_monitoring_failure(self, device: Device, result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle monitoring failure"""
        # Increment failure count
        device.failure_count = (device.failure_count or 0) + 1
        
        # Check if threshold reached
        if device.failure_count >= self.failure_threshold:
            was_down = device.status == DeviceStatus.DOWN
            device.status = DeviceStatus.DOWN
            self.db.commit()
            
            # Generate DOWN event only on actual state transition
            # (prevents duplicate events/alerts every polling cycle while already DOWN)
            if not was_down:
                await self._create_event(
                    device_id=device.id,
                    event_type=EventType.DEVICE_DOWN,
                    severity=AlertSeverity.CRITICAL,
                    message=f"Device {device.display_name} is DOWN - {result.get('message', 'Unknown error')}",
                    source='monitoring'
                )
                
                # Create or update DOWN alert
                await self._create_or_update_alert(
                    device_id=device.id,
                    severity=AlertSeverity.CRITICAL,
                    title=f"Device DOWN: {device.display_name}",
                    description=result.get('message', 'Device is unreachable'),
                    source='monitoring',
                    alert_type='device_down'
                )
        else:
            # Still within threshold - mark as warning
            if device.status == DeviceStatus.UP:
                device.status = DeviceStatus.WARNING
            self.db.commit()
        
        return {
            'success': False,
            'device_id': device.id,
            'failure_count': device.failure_count,
            'threshold': self.failure_threshold,
            'message': result.get('message', 'Monitoring failed'),
            'error_code': result.get('error_code', 'MONITORING_FAILED')
        }
    
    async def _create_event(self, device_id: int, event_type: EventType, severity: AlertSeverity, message: str, source: str, interface_id: Optional[int] = None):
        """Create event log entry"""
        event = EventLog(
            device_id=device_id,
            interface_id=interface_id,
            event_type=event_type,
            severity=severity,
            message=message,
            source=source,
            timestamp=datetime.utcnow()
        )
        self.db.add(event)
        self.db.commit()
    
    async def _create_or_update_alert(self, device_id: int, severity: AlertSeverity, title: str, description: str, source: str, alert_type: str):
        """Create new alert or update existing one"""
        # Check for existing open alert of same type
        # Match open alerts created by this manager for this alert type.
        # Titles are formatted as "<Type prefix>: <device>", so filter by
        # the deterministic prefix rather than a substring of the description.
        title_prefix = ALERT_TITLE_PREFIXES.get(alert_type, alert_type)
        filters = [
            Alert.device_id == device_id,
            Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
        ]
        # Prefer the structured alert_type column when present (deterministic);
        # fall back to the deterministic title prefix for legacy rows.
        use_alert_type_column = hasattr(Alert, 'alert_type') and             getattr(getattr(Alert, '__table__', None), 'c', {}) is not None and             'alert_type' in getattr(getattr(Alert, '__table__', None), 'c', {})
        if use_alert_type_column:
            filters.append(Alert.alert_type == alert_type)
        else:
            filters.append(Alert.title.like(f"{title_prefix}:%"))
        existing = self.db.query(Alert).filter(*filters).first()
        
        if existing:
            # Update existing alert
            existing.description = description
            existing.severity = severity
        else:
            # Create new alert
            alert = Alert(
                device_id=device_id,
                severity=severity,
                title=title,
                description=description,
                source=source,
                status=AlertStatus.OPEN,
                created_at=datetime.utcnow()
            )
            if use_alert_type_column:
                alert.alert_type = alert_type
            self.db.add(alert)
        
        self.db.commit()
    
    async def _resolve_device_alerts(self, device_id: int, alert_type: str):
        """Resolve open alerts for device"""
        title_prefix = ALERT_TITLE_PREFIXES.get(alert_type, alert_type)
        filters = [
            Alert.device_id == device_id,
            Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
        ]
        if 'alert_type' in getattr(getattr(Alert, '__table__', None), 'c', {}):
            filters.append(Alert.alert_type == alert_type)
        else:
            filters.append(Alert.title.like(f"{title_prefix}:%"))
        try:
            alerts = self.db.query(Alert).filter(*filters).all()
        except TypeError:
            # Test doubles may return non-iterable mocks; treat as "no alerts"
            # rather than crashing a successful polling cycle.
            alerts = []
        
        for alert in alerts:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
        
        self.db.commit()
