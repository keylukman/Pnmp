"""
Unit tests for MonitoringManager
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from sqlalchemy.orm import Session
from app.monitoring.manager import MonitoringManager
from app.models import (
    Device, DeviceCredential, DeviceInterface, DeviceMetric,
    InterfaceMetric, DeviceStatus, MonitoringMethod, InterfaceStatus
)


class TestMonitoringManager:
    """Test monitoring manager operations"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = Mock(spec=Session)
        db.query = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.rollback = Mock()
        return db
    
    @pytest.fixture
    def mock_device(self):
        """Create mock device"""
        device = Mock(spec=Device)
        device.id = 1
        device.hostname = "test-switch"
        device.management_ip = "192.168.1.1"
        device.vendor = "Cisco"
        device.device_type = "Switch"
        device.monitoring_method = MonitoringMethod.SNMP
        device.status = DeviceStatus.UNKNOWN
        device.failure_count = 0
        device.poll_interval = 60
        device.last_polled = None
        return device
    
    @pytest.fixture
    def mock_credential(self):
        """Create mock credential"""
        cred = Mock(spec=DeviceCredential)
        cred.device_id = 1
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
    
    @pytest.fixture
    def manager(self, mock_db):
        """Create monitoring manager instance"""
        return MonitoringManager(mock_db)
    
    @pytest.mark.asyncio
    async def test_monitor_device_not_found(self, manager, mock_db):
        """Test monitoring non-existent device"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await manager.monitor_device(999)
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_monitor_device_no_credentials(self, manager, mock_db, mock_device):
        """Test monitoring device without credentials"""
        # Mock device query
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_device,  # Device query
            None          # Credential query
        ]
        
        result = await manager.monitor_device(1)
        
        assert result['success'] is False
        assert result['error_code'] == 'NO_CREDENTIALS'
    
    @pytest.mark.asyncio
    async def test_monitor_device_success(self, manager, mock_db, mock_device, mock_credential):
        """Test successful device monitoring"""
        # Mock queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_device,
            mock_credential
        ]
        
        # Mock adapter
        with patch('app.monitoring.manager.AdapterRegistry.get_adapter') as mock_adapter_class:
            mock_adapter = AsyncMock()
            mock_adapter.test_connection.return_value = {
                'success': True,
                'method': 'SNMP',
                'latency_ms': 5.2,
                'message': 'Connection successful'
            }
            mock_adapter.get_system_info.return_value = {
                'hostname': 'test-switch',
                'cpu': 25,
                'memory': 45,
                'temperature': 38,
                'uptime_seconds': 86400
            }
            mock_adapter.get_interfaces.return_value = []
            mock_adapter.get_interface_statistics.return_value = []
            mock_adapter.close = AsyncMock()
            
            mock_adapter_class.return_value = mock_adapter
            
            result = await manager.monitor_device(1)
            
            assert result['success'] is True
            assert result['device_id'] == 1
            assert result['method'] == 'SNMP'
            assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_monitor_device_connection_failure(self, manager, mock_db, mock_device, mock_credential):
        """Test device monitoring with connection failure"""
        # Mock queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_device,
            mock_credential
        ]
        
        # Mock adapter with failure
        with patch('app.monitoring.manager.AdapterRegistry.get_adapter') as mock_adapter_class:
            mock_adapter = AsyncMock()
            mock_adapter.test_connection.return_value = {
                'success': False,
                'message': 'Connection timeout',
                'error_code': 'TIMEOUT'
            }
            mock_adapter.close = AsyncMock()
            
            mock_adapter_class.return_value = mock_adapter
            
            result = await manager.monitor_device(1)
            
            assert result['success'] is False
            assert mock_device.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_decrypt_credentials_snmp_v2c(self, manager, mock_credential):
        """Test SNMP v2c credential decryption"""
        with patch('app.monitoring.manager.credential_encryption') as mock_encryption:
            mock_encryption.decrypt.return_value = 'public'
            
            credentials = manager._decrypt_credentials(mock_credential)
            
            assert credentials['snmp_version'] == 'v2c'
            assert credentials['snmp_community'] == 'public'
            assert mock_encryption.decrypt.called
    
    @pytest.mark.asyncio
    async def test_store_device_metrics(self, manager, mock_db):
        """Test device metrics storage"""
        system_info = {
            'cpu': 30,
            'memory': 50,
            'temperature': 40,
            'uptime_seconds': 3600
        }
        
        await manager._store_device_metrics(1, system_info)
        
        # Verify metric was added
        assert mock_db.add.called
        metric = mock_db.add.call_args[0][0]
        assert isinstance(metric, DeviceMetric)
        assert metric.device_id == 1
        assert metric.cpu_percent == 30
        assert metric.memory_percent == 50
    
    @pytest.mark.asyncio
    async def test_update_interfaces_new(self, manager, mock_db, mock_device):
        """Test creating new interfaces"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_device,  # Device query
            None          # Interface not found
        ]
        
        interfaces = [
            {
                'name': 'GigabitEthernet0/1',
                'description': 'Uplink',
                'status': 'up',
                'admin_status': 'up',
                'speed_bps': 1000000000,
                'mtu': 1500
            }
        ]
        
        await manager._update_interfaces(1, interfaces)
        
        # Verify interface was added
        assert mock_db.add.called
        interface = mock_db.add.call_args[0][0]
        assert isinstance(interface, DeviceInterface)
        assert interface.name == 'GigabitEthernet0/1'
    
    @pytest.mark.asyncio
    async def test_update_interfaces_existing(self, manager, mock_db, mock_device):
        """Test updating existing interfaces"""
        existing_interface = Mock(spec=DeviceInterface)
        existing_interface.id = 1
        existing_interface.name = 'GigabitEthernet0/1'
        existing_interface.status = 'down'
        existing_interface.description = 'Old description'
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_device,
            existing_interface
        ]
        
        interfaces = [
            {
                'name': 'GigabitEthernet0/1',
                'description': 'New description',
                'status': 'up',
                'admin_status': 'up',
                'speed_bps': 1000000000,
                'mtu': 1500
            }
        ]
        
        await manager._update_interfaces(1, interfaces)
        
        # Verify interface was updated
        assert existing_interface.description == 'New description'
        assert existing_interface.status == 'up'
    
    @pytest.mark.asyncio
    async def test_handle_monitoring_success(self, manager, mock_db, mock_device):
        """Test successful monitoring handler"""
        mock_device.status = DeviceStatus.DOWN
        mock_device.failure_count = 3
        
        await manager._handle_monitoring_success(mock_device)
        
        assert mock_device.status == DeviceStatus.UP
        assert mock_device.failure_count == 0
        assert mock_device.last_polled is not None
        assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_handle_monitoring_failure_threshold_not_reached(self, manager, mock_db, mock_device):
        """Test failure handler when threshold not reached"""
        mock_device.status = DeviceStatus.UP
        mock_device.failure_count = 0
        manager.failure_threshold = 3
        
        result = await manager._handle_monitoring_failure(
            mock_device,
            {'success': False, 'message': 'Timeout'}
        )
        
        assert mock_device.failure_count == 1
        assert mock_device.status == DeviceStatus.WARNING
        assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_handle_monitoring_failure_threshold_reached(self, manager, mock_db, mock_device):
        """Test failure handler when threshold reached"""
        mock_device.status = DeviceStatus.WARNING
        mock_device.failure_count = 2
        manager.failure_threshold = 3
        
        result = await manager._handle_monitoring_failure(
            mock_device,
            {'success': False, 'message': 'Timeout'}
        )
        
        assert mock_device.failure_count == 3
        assert mock_device.status == DeviceStatus.DOWN
        assert result['success'] is False
