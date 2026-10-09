"""
Unit tests for monitoring manager
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.monitoring.manager import MonitoringManager
from app.models import (
    Device, DeviceCredential, DeviceInterface, DeviceMetric,
    InterfaceMetric, Alert, EventLog, DeviceStatus, AlertSeverity,
    AlertStatus, EventType, MonitoringMethod, InterfaceStatus
)


class TestMonitoringManager:
    """Test monitoring manager functionality"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        session = Mock(spec=Session)
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        return session
    
    @pytest.fixture
    def manager(self, mock_db_session):
        """Create a manager instance"""
        return MonitoringManager(mock_db_session)
    
    @pytest.fixture
    def mock_device(self):
        """Create a mock device"""
        device = Mock(spec=Device)
        device.id = 1
        device.display_name = "Test Device"
        device.management_ip = "192.168.1.1"
        device.vendor = "Cisco"
        device.device_type = "Switch"
        device.monitoring_method = MonitoringMethod.SNMP
        device.status = DeviceStatus.UNKNOWN
        device.failure_count = 0
        device.last_polled = None
        return device
    
    @pytest.fixture
    def mock_credential(self):
        """Create a mock credential"""
        cred = Mock(spec=DeviceCredential)
        cred.snmp_version = "v2c"
        cred.snmp_community_encrypted = "encrypted_community"
        cred.snmp_username = None
        cred.snmp_auth_password_encrypted = None
        cred.snmp_auth_protocol = None
        cred.snmp_privacy_password_encrypted = None
        cred.snmp_privacy_protocol = None
        cred.username = None
        cred.encrypted_password = None
        cred.ssh_enabled = False
        cred.api_enabled = False
        return cred
    
    def test_manager_initialization(self, manager):
        """Test manager initializes correctly"""
        assert manager.failure_threshold == 3  # Default from settings
    
    @pytest.mark.asyncio
    async def test_monitor_device_not_found(self, manager, mock_db_session):
        """Test monitoring non-existent device"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = await manager.monitor_device(999)
        
        assert result['success'] is False
        assert result['error'] == 'Device not found'
    
    @pytest.mark.asyncio
    async def test_monitor_device_no_credentials(self, manager, mock_db_session, mock_device):
        """Test monitoring device without credentials"""
        # Mock device query
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_device,  # Device query
            None  # Credential query
        ]
        
        result = await manager.monitor_device(1)
        
        assert result['success'] is False
        assert result['error'] == 'No credentials configured'
        assert result['error_code'] == 'NO_CREDENTIALS'
    
    @pytest.mark.asyncio
    async def test_decrypt_credentials_snmp_v2c(self, manager, mock_credential):
        """Test decrypting SNMP v2c credentials"""
        with patch('app.monitoring.manager.credential_encryption') as mock_encryption:
            mock_encryption.decrypt.return_value = "public"
            
            credentials = manager._decrypt_credentials(mock_credential)
            
            assert credentials['snmp_version'] == "v2c"
            assert credentials['snmp_community'] == "public"
            assert credentials['ssh_enabled'] is False
            assert credentials['api_enabled'] is False
    
    @pytest.mark.asyncio
    async def test_handle_monitoring_success(self, manager, mock_db_session, mock_device):
        """Test handling successful monitoring"""
        mock_device.status = DeviceStatus.DOWN
        mock_device.failure_count = 3
        
        await manager._handle_monitoring_success(mock_device)
        
        assert mock_device.failure_count == 0
        assert mock_device.status == DeviceStatus.UP
        assert mock_device.last_polled is not None
        assert mock_device.last_seen is not None
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_handle_monitoring_success_recovery_event(self, manager, mock_db_session, mock_device):
        """Test that recovery event is generated when device comes back up"""
        mock_device.status = DeviceStatus.DOWN
        
        await manager._handle_monitoring_success(mock_device)
        
        # Should create an event
        mock_db_session.add.assert_called()
        added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
        events = [obj for obj in added_objects if isinstance(obj, EventLog)]
        assert len(events) > 0
        assert events[0].event_type == EventType.DEVICE_UP
    
    @pytest.mark.asyncio
    async def test_handle_monitoring_failure_below_threshold(self, manager, mock_db_session, mock_device):
        """Test handling failure below threshold"""
        mock_device.status = DeviceStatus.UP
        mock_device.failure_count = 0
        
        result = await manager._handle_monitoring_failure(mock_device, {
            'success': False,
            'message': 'Connection timeout'
        })
        
        assert mock_device.failure_count == 1
        assert mock_device.status == DeviceStatus.WARNING
        assert result['success'] is False
        assert result['failure_count'] == 1
    
    @pytest.mark.asyncio
    async def test_handle_monitoring_failure_at_threshold(self, manager, mock_db_session, mock_device):
        """Test handling failure at threshold"""
        mock_device.status = DeviceStatus.UP
        mock_device.failure_count = 2  # One more will hit threshold of 3
        
        result = await manager._handle_monitoring_failure(mock_device, {
            'success': False,
            'message': 'Connection timeout'
        })
        
        assert mock_device.failure_count == 3
        assert mock_device.status == DeviceStatus.DOWN
        assert result['success'] is False
        assert result['failure_count'] == 3
        
        # Should create an alert
        mock_db_session.add.assert_called()
        added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
        alerts = [obj for obj in added_objects if isinstance(obj, Alert)]
        assert len(alerts) > 0
        assert alerts[0].severity == AlertSeverity.CRITICAL
    
    @pytest.mark.asyncio
    async def test_store_device_metrics(self, manager, mock_db_session):
        """Test storing device metrics"""
        system_info = {
            'cpu': 45,
            'memory': 60,
            'temperature': 35,
            'uptime_seconds': 86400
        }
        
        await manager._store_device_metrics(1, system_info)
        
        mock_db_session.add.assert_called()
        added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
        metrics = [obj for obj in added_objects if isinstance(obj, DeviceMetric)]
        assert len(metrics) == 1
        assert metrics[0].cpu_percent == 45
        assert metrics[0].memory_percent == 60
        assert metrics[0].temperature == 35
        assert metrics[0].uptime_seconds == 86400
    
    @pytest.mark.asyncio
    async def test_update_interfaces_new(self, manager, mock_db_session, mock_device):
        """Test creating new interfaces"""
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_device,  # Device query
            None  # Interface query (doesn't exist)
        ]
        
        interfaces = [
            {
                'name': 'GigabitEthernet0/1',
                'description': 'Uplink',
                'status': 'up',
                'admin_status': 'up',
                'speed_bps': 1000000000
            }
        ]
        
        await manager._update_interfaces(1, interfaces)
        
        mock_db_session.add.assert_called()
        added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
        new_interfaces = [obj for obj in added_objects if isinstance(obj, DeviceInterface)]
        assert len(new_interfaces) == 1
        assert new_interfaces[0].name == 'GigabitEthernet0/1'
    
    @pytest.mark.asyncio
    async def test_update_interfaces_status_change(self, manager, mock_db_session, mock_device):
        """Test interface status change detection"""
        existing_interface = Mock(spec=DeviceInterface)
        existing_interface.id = 1
        existing_interface.name = 'GigabitEthernet0/1'
        existing_interface.status = 'down'
        
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_device,  # Device query
            existing_interface  # Interface query (exists)
        ]
        
        interfaces = [
            {
                'name': 'GigabitEthernet0/1',
                'description': 'Uplink',
                'status': 'up',  # Changed from down to up
                'admin_status': 'up',
                'speed_bps': 1000000000
            }
        ]
        
        await manager._update_interfaces(1, interfaces)
        
        # Should create an event for status change
        mock_db_session.add.assert_called()
        added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
        events = [obj for obj in added_objects if isinstance(obj, EventLog)]
        assert len(events) > 0
        assert events[0].event_type == EventType.INTERFACE_UP
    
    @pytest.mark.asyncio
    async def test_store_interface_metrics_with_calculation(self, manager, mock_db_session):
        """Test storing interface metrics with traffic calculation"""
        # Mock existing interface
        existing_interface = Mock(spec=DeviceInterface)
        existing_interface.id = 1
        existing_interface.name = 'GigabitEthernet0/1'
        existing_interface.rx_bytes = 1000000
        existing_interface.tx_bytes = 500000
        existing_interface.last_polled = datetime.utcnow() - timedelta(seconds=10)
        existing_interface.speed_bps = 1000000000
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = existing_interface
        
        stats = [
            {
                'name': 'GigabitEthernet0/1',
                'rx_bytes': 2000000,  # 1 MB increase
                'tx_bytes': 1000000,  # 500 KB increase
                'rx_errors': 0,
                'tx_errors': 0,
                'rx_discards': 0,
                'tx_discards': 0
            }
        ]
        
        await manager._store_interface_metrics(1, stats)
        
        # Should create metric
        mock_db_session.add.assert_called()
        added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
        metrics = [obj for obj in added_objects if isinstance(obj, InterfaceMetric)]
        assert len(metrics) == 1
        
        # Verify traffic calculation
        # 1 MB in 10 seconds = 800 Kbps
        assert metrics[0].rx_bps is not None
        assert metrics[0].tx_bps is not None
    
    @pytest.mark.asyncio
    async def test_create_or_update_alert_new(self, manager, mock_db_session):
        """Test creating new alert"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        await manager._create_or_update_alert(
            device_id=1,
            severity=AlertSeverity.CRITICAL,
            title="Device DOWN: Test",
            description="Device is unreachable",
            source='monitoring',
            alert_type='device_down'
        )
        
        mock_db_session.add.assert_called()
        added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
        alerts = [obj for obj in added_objects if isinstance(obj, Alert)]
        assert len(alerts) == 1
        assert alerts[0].status == AlertStatus.OPEN
    
    @pytest.mark.asyncio
    async def test_create_or_update_alert_existing(self, manager, mock_db_session):
        """Test updating existing alert"""
        existing_alert = Mock(spec=Alert)
        existing_alert.status = AlertStatus.OPEN
        existing_alert.description = "Old description"
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = existing_alert
        
        await manager._create_or_update_alert(
            device_id=1,
            severity=AlertSeverity.CRITICAL,
            title="Device DOWN: Test",
            description="New description",
            source='monitoring',
            alert_type='device_down'
        )
        
        # Should update existing alert, not create new one
        assert existing_alert.description == "New description"
        mock_db_session.add.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_resolve_device_alerts(self, manager, mock_db_session):
        """Test resolving device alerts"""
        alert1 = Mock(spec=Alert)
        alert1.status = AlertStatus.OPEN
        alert2 = Mock(spec=Alert)
        alert2.status = AlertStatus.ACKNOWLEDGED
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [alert1, alert2]
        
        await manager._resolve_device_alerts(1, 'device_down')
        
        assert alert1.status == AlertStatus.RESOLVED
        assert alert2.status == AlertStatus.RESOLVED
        assert alert1.resolved_at is not None
        assert alert2.resolved_at is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
