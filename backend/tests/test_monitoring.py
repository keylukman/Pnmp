"""
Unit tests for monitoring system
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.monitoring.manager import MonitoringManager
from app.monitoring.scheduler import MonitoringScheduler
from app.monitoring.adapters.base import NetworkDeviceAdapter
from app.models import (
    Device, DeviceInterface, DeviceMetric, InterfaceMetric,
    DeviceStatus, EventType, AlertSeverity
)


class MockAdapter(NetworkDeviceAdapter):
    """Mock adapter for testing"""
    
    def __init__(self, device_id: int, management_ip: str, credentials: dict):
        super().__init__(device_id, management_ip, credentials)
        self.test_connection_result = {'success': True, 'latency_ms': 5.0}
        self.system_info_result = {
            'hostname': 'test-device',
            'cpu': 25,
            'memory': 45,
            'temperature': 35,
            'uptime_seconds': 86400
        }
        self.interfaces_result = [
            {
                'name': 'eth0',
                'status': 'up',
                'speed_bps': 1000000000,
                'description': 'Test interface'
            }
        ]
        self.interface_stats_result = [
            {
                'name': 'eth0',
                'rx_bytes': 1000000,
                'tx_bytes': 500000,
                'rx_errors': 0,
                'tx_errors': 0
            }
        ]
    
    async def test_connection(self):
        return self.test_connection_result
    
    async def get_system_info(self):
        return self.system_info_result
    
    async def get_interfaces(self):
        return self.interfaces_result
    
    async def get_interface_statistics(self):
        return self.interface_stats_result
    
    async def close(self):
        pass


class TestMonitoringManager:
    """Test MonitoringManager"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = Mock(spec=Session)
        return db
    
    @pytest.fixture
    def mock_device(self):
        """Create mock device"""
        device = Mock(spec=Device)
        device.id = 1
        device.display_name = 'Test Device'
        device.management_ip = '192.168.1.1'
        device.vendor = 'Generic'
        device.device_type = 'Switch'
        device.monitoring_method = Mock()
        device.monitoring_method.value = 'snmp'
        device.status = DeviceStatus.UNKNOWN
        device.failure_count = 0
        return device
    
    @pytest.mark.asyncio
    async def test_monitor_device_success(self, mock_db, mock_device):
        """Test successful device monitoring"""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = mock_device
        
        with patch('app.monitoring.manager.AdapterRegistry.get_adapter') as mock_get_adapter:
            mock_adapter = MockAdapter(1, '192.168.1.1', {})
            mock_get_adapter.return_value = mock_adapter
            
            manager = MonitoringManager(mock_db)
            result = await manager.monitor_device(1)
            
            assert result['success'] is True
            assert result['device_id'] == 1
    
    @pytest.mark.asyncio
    async def test_monitor_device_no_credentials(self, mock_db, mock_device):
        """Test monitoring with no credentials"""
        # Setup mocks - device exists but no credentials
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_device, None]
        
        manager = MonitoringManager(mock_db)
        result = await manager.monitor_device(1)
        
        assert result['success'] is False
        assert result['error_code'] == 'NO_CREDENTIALS'
    
    @pytest.mark.asyncio
    async def test_counter_delta_calculation(self, mock_db):
        """Test counter delta calculation for traffic"""
        # Create mock interface with previous values
        mock_interface = Mock(spec=DeviceInterface)
        mock_interface.id = 1
        mock_interface.name = 'eth0'
        mock_interface.device_id = 1
        mock_interface.rx_bytes = 1000000
        mock_interface.tx_bytes = 500000
        mock_interface.speed_bps = 1000000000
        mock_interface.last_polled = datetime.utcnow() - timedelta(seconds=10)
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_interface
        
        manager = MonitoringManager(mock_db)
        
        # Simulate new stats
        stats = [{
            'name': 'eth0',
            'rx_bytes': 2000000,  # Delta: 1000000 bytes in 10 seconds
            'tx_bytes': 1000000,  # Delta: 500000 bytes in 10 seconds
            'rx_errors': 0,
            'tx_errors': 0
        }]
        
        await manager._store_interface_metrics(1, stats)
        
        # Verify metrics were created
        assert mock_db.add.called
        
        # Get the InterfaceMetric that was added
        added_metric = mock_db.add.call_args[0][0]
        assert isinstance(added_metric, InterfaceMetric)
        
        # Calculate expected bps
        # RX: 1000000 bytes * 8 bits / 10 seconds = 800000 bps
        # TX: 500000 bytes * 8 bits / 10 seconds = 400000 bps
        expected_rx_bps = 800000
        expected_tx_bps = 400000
        
        assert added_metric.rx_bps == expected_rx_bps
        assert added_metric.tx_bps == expected_tx_bps
    
    @pytest.mark.asyncio
    async def test_counter_reset_handling(self, mock_db):
        """Test counter reset detection"""
        # Create mock interface with previous values
        mock_interface = Mock(spec=DeviceInterface)
        mock_interface.id = 1
        mock_interface.name = 'eth0'
        mock_interface.device_id = 1
        mock_interface.rx_bytes = 2000000
        mock_interface.tx_bytes = 1000000
        mock_interface.speed_bps = 1000000000
        mock_interface.last_polled = datetime.utcnow() - timedelta(seconds=10)
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_interface
        
        manager = MonitoringManager(mock_db)
        
        # Simulate counter reset (current < previous)
        stats = [{
            'name': 'eth0',
            'rx_bytes': 1000000,  # Less than previous - counter reset
            'tx_bytes': 500000,
            'rx_errors': 0,
            'tx_errors': 0
        }]
        
        await manager._store_interface_metrics(1, stats)
        
        # Get the InterfaceMetric that was added
        added_metric = mock_db.add.call_args[0][0]
        
        # Should be 0 due to counter reset
        assert added_metric.rx_bps == 0
        assert added_metric.tx_bps == 0


class TestMonitoringScheduler:
    """Test MonitoringScheduler"""
    
    @pytest.fixture
    def mock_session_factory(self):
        """Create mock session factory"""
        def factory():
            return Mock(spec=Session)
        return factory
    
    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self, mock_session_factory):
        """Test scheduler start and stop"""
        scheduler = MonitoringScheduler(mock_session_factory)
        
        # Start scheduler
        await scheduler.start()
        assert scheduler.running is True
        
        # Stop scheduler
        await scheduler.stop()
        assert scheduler.running is False
    
    def test_scheduler_status(self, mock_session_factory):
        """Test scheduler status reporting"""
        scheduler = MonitoringScheduler(mock_session_factory)
        
        status = scheduler.get_status()
        
        assert 'running' in status
        assert 'interval' in status
        assert 'max_concurrency' in status
        assert 'total_polls' in status
        assert 'successful_polls' in status
        assert 'failed_polls' in status


class TestUtilizationCalculation:
    """Test utilization calculation"""
    
    def test_utilization_calculation(self):
        """Test interface utilization calculation"""
        speed_bps = 1000000000  # 1 Gbps
        traffic_bps = 500000000  # 500 Mbps
        
        utilization = min(100, int((traffic_bps / speed_bps) * 100))
        
        assert utilization == 50
    
    def test_utilization_clamping(self):
        """Test utilization is clamped to 100%"""
        speed_bps = 1000000000  # 1 Gbps
        traffic_bps = 1500000000  # 1.5 Gbps (over capacity)
        
        utilization = min(100, int((traffic_bps / speed_bps) * 100))
        
        assert utilization == 100
    
    def test_utilization_unknown_speed(self):
        """Test utilization with unknown speed"""
        speed_bps = None
        traffic_bps = 500000000
        
        if speed_bps and speed_bps > 0:
            utilization = min(100, int((traffic_bps / speed_bps) * 100))
        else:
            utilization = 0
        
        assert utilization == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
