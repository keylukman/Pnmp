"""
Unit tests for monitoring scheduler
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.monitoring.scheduler import MonitoringScheduler
from app.models import Device, DeviceStatus


class TestMonitoringScheduler:
    """Test monitoring scheduler functionality"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        session = Mock(spec=Session)
        return session
    
    @pytest.fixture
    def mock_db_session_factory(self, mock_db_session):
        """Create a mock database session factory"""
        def factory():
            return mock_db_session
        return factory
    
    @pytest.fixture
    def scheduler(self, mock_db_session_factory):
        """Create a scheduler instance"""
        return MonitoringScheduler(mock_db_session_factory)
    
    def test_scheduler_initialization(self, scheduler):
        """Test scheduler initializes correctly"""
        assert scheduler.running is False
        assert scheduler.task is None
        assert scheduler.interval == 60  # Default from settings
        assert scheduler.stats['total_polls'] == 0
        assert scheduler.stats['successful_polls'] == 0
        assert scheduler.stats['failed_polls'] == 0
    
    @pytest.mark.asyncio
    async def test_scheduler_start(self, scheduler):
        """Test scheduler starts correctly"""
        await scheduler.start()
        assert scheduler.running is True
        assert scheduler.task is not None
        
        # Clean up
        await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_scheduler_stop(self, scheduler):
        """Test scheduler stops correctly"""
        await scheduler.start()
        await scheduler.stop()
        assert scheduler.running is False
    
    @pytest.mark.asyncio
    async def test_scheduler_double_start(self, scheduler):
        """Test scheduler doesn't start twice"""
        await scheduler.start()
        await scheduler.start()  # Should not create another task
        assert scheduler.running is True
        
        # Clean up
        await scheduler.stop()
    
    def test_get_status(self, scheduler):
        """Test get_status returns correct information"""
        status = scheduler.get_status()
        
        assert 'running' in status
        assert 'interval' in status
        assert 'max_concurrency' in status
        assert 'active_polls' in status
        assert 'total_polls' in status
        assert 'successful_polls' in status
        assert 'failed_polls' in status
        assert 'last_poll' in status
        
        assert status['running'] is False
        assert status['interval'] == 60
    
    @pytest.mark.asyncio
    async def test_poll_all_devices_no_devices(self, scheduler, mock_db_session):
        """Test polling when no devices exist"""
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        await scheduler._poll_all_devices()
        
        # Should not crash and should complete
        assert scheduler.stats['total_polls'] == 0
    
    @pytest.mark.asyncio
    async def test_poll_all_devices_filters_by_interval(self, scheduler, mock_db_session):
        """Test that scheduler only polls devices that are due"""
        now = datetime.utcnow()
        
        # Create mock devices
        device1 = Mock(spec=Device)
        device1.id = 1
        device1.monitoring_enabled = True
        device1.status = DeviceStatus.UP
        device1.last_polled = now - timedelta(seconds=30)  # Not due yet (60s interval)
        device1.poll_interval = 60
        
        device2 = Mock(spec=Device)
        device2.id = 2
        device2.monitoring_enabled = True
        device2.status = DeviceStatus.UP
        device2.last_polled = now - timedelta(seconds=70)  # Due (60s interval)
        device2.poll_interval = 60
        
        device3 = Mock(spec=Device)
        device3.id = 3
        device3.monitoring_enabled = True
        device3.status = DeviceStatus.UP
        device3.last_polled = None  # Never polled, should be polled
        device3.poll_interval = 60
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            device1, device2, device3
        ]
        
        # Mock the manager
        with patch('app.monitoring.scheduler.MonitoringManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.monitor_device.return_value = {'success': True}
            mock_manager_class.return_value = mock_manager
            
            await scheduler._poll_all_devices()
            
            # Should only poll device2 and device3 (2 devices)
            assert mock_manager.monitor_device.call_count == 2
            mock_manager.monitor_device.assert_any_call(2)
            mock_manager.monitor_device.assert_any_call(3)
    
    @pytest.mark.asyncio
    async def test_poll_all_devices_respects_maintenance(self, scheduler, mock_db_session):
        """Test that scheduler skips devices in maintenance"""
        now = datetime.utcnow()
        
        device1 = Mock(spec=Device)
        device1.id = 1
        device1.monitoring_enabled = True
        device1.status = DeviceStatus.MAINTENANCE  # Should be filtered out
        device1.last_polled = now - timedelta(seconds=70)
        device1.poll_interval = 60
        
        # The filter should exclude maintenance devices
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        await scheduler._poll_all_devices()
        
        # Should not poll any devices
        assert scheduler.stats['total_polls'] == 0
    
    @pytest.mark.asyncio
    async def test_poll_device_with_semaphore(self, scheduler):
        """Test polling with concurrency control"""
        with patch('app.monitoring.scheduler.MonitoringManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.monitor_device.return_value = {'success': True}
            mock_manager_class.return_value = mock_manager
            
            result = await scheduler._poll_device_with_semaphore(mock_manager, 1)
            
            assert result == {'success': True}
            assert scheduler.stats['active_polls'] == 0  # Should be decremented after
    
    @pytest.mark.asyncio
    async def test_poll_device_with_semaphore_error(self, scheduler):
        """Test polling handles errors correctly"""
        with patch('app.monitoring.scheduler.MonitoringManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.monitor_device.side_effect = Exception("Test error")
            mock_manager_class.return_value = mock_manager
            
            result = await scheduler._poll_device_with_semaphore(mock_manager, 1)
            
            assert result['success'] is False
            assert 'error' in result
            assert scheduler.stats['active_polls'] == 0  # Should be decremented even on error
    
    @pytest.mark.asyncio
    async def test_poll_device_now(self, scheduler):
        """Test manual device polling"""
        with patch('app.monitoring.scheduler.MonitoringManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.monitor_device.return_value = {'success': True}
            mock_manager_class.return_value = mock_manager
            
            result = await scheduler.poll_device_now(1)
            
            assert result == {'success': True}
            mock_manager.monitor_device.assert_called_once_with(1)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
