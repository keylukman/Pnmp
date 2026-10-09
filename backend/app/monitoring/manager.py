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
from .calculator import TrafficCalculator
from ..models import (
    Device, DeviceCredential, DeviceInterface, DeviceMetric,
    InterfaceMetric, Alert, EventLog, DeviceStatus, AlertSeverity,
    AlertStatus, EventType, MonitoringMethod, InterfaceStatus
)
from ..core.encryption import credential_encryption
from ..core.config import settings

logger = logging.getLogger(__name__)


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
        Monitor a single device with proper transaction management.
        Returns monitoring result with status and metrics.
        """
        async with self.concurrency_limit:
            try:
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
                
                # Get adapter
                adapter = AdapterRegistry.get_adapter(
                    device_id=device.id,
                    management_ip=device.management_ip,
                    vendor=device.vendor,
                    device_type=device.device_type,
                    monitoring_method=device.monitoring_method.value if device.monitoring_method else 'snmp',
                    credentials=credentials
                )
                
                try:
                    # Test connection
                    conn_result = await adapter.test_connection()
                    
                    if not conn_result.get('success'):
                        # Handle failure
                        result = await self._handle_monitoring_failure(device, conn_result)
                        self.db.commit()  # Commit failure state
                        return result
                    
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
                    interfaces = await adapter.get_interfaces()
                    if interfaces:
                        result['interfaces'] = interfaces
                        
                        # Update/create interfaces
                        await self._update_interfaces(device_id, interfaces)
                    
                    # Get interface statistics
                    stats = await adapter.get_interface_statistics()
                    if stats:
                        result['interface_stats'] = stats
                        
                        # Store interface metrics
                        await self._store_interface_metrics(device_id, stats)
                    
                    # Update device status
                    await self._handle_monitoring_success(device)
                    
                    # Commit all changes in one transaction
                    self.db.commit()
                    
                    return result
                    
                except Exception as e:
                    self.db.rollback()  # Rollback on error
                    logger.error(f"Error monitoring device {device_id}: {e}")
                    return await self._handle_monitoring_failure(device, {
                        'success': False,
                        'message': str(e),
                        'error_code': 'MONITORING_ERROR'
                    })
                finally:
                    await adapter.close()
                    
            except Exception as e:
                self.db.rollback()
                logger.error(f"Critical error in monitor_device {device_id}: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'error_code': 'CRITICAL_ERROR'
                }
    
    def _decrypt_credentials(self, cred: DeviceCredential) -> Dict[str, Any]:
        """Decrypt device credentials"""
        credentials = {
            'snmp_version': cred.snmp_version or 'v2c',
            'timeout': settings.SNMP_TIMEOUT,
            'retries': settings.SNMP_RETRIES,
            'ssh_enabled': cred.ssh_enabled,
            'api_enabled': cred.api_enabled
        }
        
        # Decrypt SNMP community (v2c)
        if cred.snmp_community_encrypted:
            try:
                credentials['snmp_community'] = credential_encryption.decrypt(
                    cred.snmp_community_encrypted
                )
            except:
                credentials['snmp_community'] = 'public'
        
        # Decrypt SNMP v3 credentials
        if cred.snmp_username:
            credentials['snmp_username'] = cred.snmp_username
        
        if cred.snmp_auth_password_encrypted:
            try:
                credentials['snmp_auth_password'] = credential_encryption.decrypt(
                    cred.snmp_auth_password_encrypted
                )
            except:
                pass
        
        if cred.snmp_auth_protocol:
            credentials['snmp_auth_protocol'] = cred.snmp_auth_protocol
        
        if cred.snmp_privacy_password_encrypted:
            try:
                credentials['snmp_privacy_password'] = credential_encryption.decrypt(
                    cred.snmp_privacy_password_encrypted
                )
            except:
                pass
        
        if cred.snmp_privacy_protocol:
            credentials['snmp_privacy_protocol'] = cred.snmp_privacy_protocol
        
        # Decrypt SSH/API credentials
        if cred.username:
            credentials['username'] = cred.username
        
        if cred.encrypted_password:
            try:
                credentials['password'] = credential_encryption.decrypt(
                    cred.encrypted_password
                )
            except:
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
        # No commit here - will be committed by caller
    
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
        
        # No commit here - will be committed by caller
    
    async def _store_interface_metrics(self, device_id: int, stats: List[Dict[str, Any]]):
        """Store interface traffic metrics with proper counter delta calculation"""
        now = datetime.utcnow()
        
        for stat in stats:
            # Find interface
            iface = self.db.query(DeviceInterface).filter(
                DeviceInterface.device_id == device_id,
                DeviceInterface.name == stat.get('name')
            ).first()
            
            if not iface:
                continue
            
            # Get current counter values
            current_rx_bytes = stat.get('rx_bytes', 0)
            current_tx_bytes = stat.get('tx_bytes', 0)
            
            # Use TrafficCalculator for proper calculation
            metrics = TrafficCalculator.calculate_interface_metrics(
                current_rx_bytes=current_rx_bytes,
                current_tx_bytes=current_tx_bytes,
                previous_rx_bytes=iface.rx_bytes,
                previous_tx_bytes=iface.tx_bytes,
                current_time=now,
                previous_time=iface.last_polled,
                speed_bps=iface.speed_bps
            )
            
            # Log counter reset if detected
            if metrics['is_counter_reset']:
                logger.info(f"Counter reset detected on device {device_id}, interface {iface.name}")
            
            # Store metric with NULL values where appropriate
            metric = InterfaceMetric(
                interface_id=iface.id,
                device_id=device_id,
                timestamp=now,
                rx_bytes=current_rx_bytes,
                tx_bytes=current_tx_bytes,
                rx_bps=metrics['rx_bps'],  # Can be None
                tx_bps=metrics['tx_bps'],  # Can be None
                rx_errors=stat.get('rx_errors', 0),
                tx_errors=stat.get('tx_errors', 0),
                rx_discards=stat.get('rx_discards', 0),
                tx_discards=stat.get('tx_discards', 0),
                utilization_in=metrics['utilization_in'],  # Can be None
                utilization_out=metrics['utilization_out']  # Can be None
            )
            self.db.add(metric)
            
            # Update interface current values
            iface.rx_bytes = current_rx_bytes
            iface.tx_bytes = current_tx_bytes
            iface.rx_bps = metrics['rx_bps'] if metrics['rx_bps'] is not None else 0
            iface.tx_bps = metrics['tx_bps'] if metrics['tx_bps'] is not None else 0
            iface.rx_errors = stat.get('rx_errors', 0)
            iface.tx_errors = stat.get('tx_errors', 0)
            iface.rx_discards = stat.get('rx_discards', 0)
            iface.tx_discards = stat.get('tx_discards', 0)
            iface.utilization_in = metrics['utilization_in'] if metrics['utilization_in'] is not None else 0
            iface.utilization_out = metrics['utilization_out'] if metrics['utilization_out'] is not None else 0
            
            # Calculate max utilization for display
            util_in = metrics['utilization_in'] if metrics['utilization_in'] is not None else 0
            util_out = metrics['utilization_out'] if metrics['utilization_out'] is not None else 0
            iface.utilization = max(util_in, util_out)
            iface.last_polled = now
        
        # No commit here - will be committed by caller
    
    async def _handle_monitoring_success(self, device: Device):
        """Handle successful monitoring"""
        # Reset failure count
        device.failure_count = 0
        device.last_seen = datetime.utcnow()
        device.last_polled = datetime.utcnow()  # Track last poll time for scheduler
        
        # Check if device was down
        was_down = device.status == DeviceStatus.DOWN
        device.status = DeviceStatus.UP
        
        # No commit here - will be committed by caller
        
        # Generate recovery event if was down
        if was_down:
            await self._create_event(
                device_id=device.id,
                event_type=EventType.DEVICE_UP,
                severity=AlertSeverity.INFO,
                message=f"Device {device.display_name} is now UP",
                source='monitoring'
            )
            
            # Resolve any open DOWN alerts
            await self._resolve_device_alerts(device.id, 'device_down')
    
    async def _handle_monitoring_failure(self, device: Device, result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle monitoring failure"""
        # Increment failure count
        device.failure_count = (device.failure_count or 0) + 1
        
        # Check if threshold reached
        if device.failure_count >= self.failure_threshold:
            was_up = device.status == DeviceStatus.UP
            device.status = DeviceStatus.DOWN
            # No commit here - will be committed by caller
            
            # Generate DOWN event
            if was_up or device.status == DeviceStatus.DOWN:
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
            # No commit here - will be committed by caller
        
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
        # No commit here - will be committed by caller
    
    async def _create_or_update_alert(self, device_id: int, severity: AlertSeverity, title: str, description: str, source: str, alert_type: str):
        """Create new alert or update existing one"""
        # Check for existing open alert of same type
        existing = self.db.query(Alert).filter(
            Alert.device_id == device_id,
            Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
            Alert.title.like(f"%{alert_type}%")
        ).first()
        
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
            self.db.add(alert)
        
        # No commit here - will be committed by caller
    
    async def _resolve_device_alerts(self, device_id: int, alert_type: str):
        """Resolve open alerts for device"""
        alerts = self.db.query(Alert).filter(
            Alert.device_id == device_id,
            Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
            Alert.title.like(f"%{alert_type}%")
        ).all()
        
        for alert in alerts:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
        
        # No commit here - will be committed by caller
