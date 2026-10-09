"""
Unit tests for MonitoringScheduler
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from app.monitoring.scheduler import MonitoringScheduler, init_scheduler, get_scheduler


class TestMonitoringScheduler:
    """Test monitoring scheduler operations"""
    
    @pytest.fixture
    def mock_db_session_factory(self):
        """Create mock database session factory"""
        factory = Mock()
        session = Mock()
        session.query = Mock()
        session.close = Mock()
        factory.return_value = session
        return factory
    
    @pytest.fixture
    def scheduler(self, mock_db_session_factory):
        """Create scheduler instance"""
        return MonitoringScheduler(mock_db_session_factory)
    
    def test_scheduler_initialization(self, scheduler):
        """Test scheduler initialization"""
        assert scheduler.running is False
        assert scheduler.task is None
        assert scheduler.interval == 60
        assert scheduler.stats['total_polls'] == 0
        assert scheduler.stats['successful_polls'] == 0
        assert scheduler.stats['failed_polls'] == 0
    
    @pytest.mark.asyncio
    async def test_scheduler_start(self, scheduler):
        """Test scheduler start"""
        await scheduler.start()
        
        assert scheduler.running is True
        assert scheduler.task is not None
        
        # Cleanup
        await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_scheduler_stop(self, scheduler):
        """Test scheduler stop"""
        await scheduler.start()
        await scheduler.stop()
        
        assert scheduler.running is False
    
    @pytest.mark.asyncio
    async def test_scheduler_start_already_running(self, scheduler):
        """Test starting already running scheduler"""
        await scheduler.start()
        
        # Try to start again
        with patch('app.monitoring.scheduler.logger') as mock_logger:
            await scheduler.start()
            mock_logger.warning.assert_called_once()
        
        # Cleanup
        await scheduler.stop()
    
    def test_get_status(self, scheduler):
        """Test get scheduler status"""
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
    async def test_poll_all_devices_no_devices(self, scheduler, mock_db_session_factory):
        """Test polling when no devices exist"""
        session = mock_db_session_factory.return_value
        session.query.return_value.filter.return_value.all.return_value = []
        
        await scheduler._poll_all_devices()
        
        # Should not crash
        assert scheduler.stats['total_polls'] == 0
    
    @pytest.mark.asyncio
    async def test_poll_all_devices_with_devices(self, scheduler, mock_db_session_factory):
        """Test polling with devices"""
        # Mock device
        mock_device = Mock()
        mock_device.id = 1
        mock_device.last_polled = None
        
        session = mock_db_session_factory.return_value
        session.query.return_value.filter.return_value.all.return_value = [mock_device]
        
        # Mock manager
        with patch('app.monitoring.scheduler.MonitoringManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.monitor_device.return_value = {'success': True}
            mock_manager_class.return_value = mock_manager
            
            await scheduler._poll_all_devices()
            
            # Verify polling occurred
            assert mock_manager.monitor_device.called
    
    @pytest.mark.asyncio
    async def test_poll_device_with_semaphore(self, scheduler):
        """Test polling device with semaphore"""
        mock_manager = AsyncMock()
        mock_manager.monitor_device.return_value = {'success': True}
        
        result = await scheduler._poll_device_with_semaphore(mock_manager, 1)
        
        assert result['success'] is True
        assert scheduler.stats['active_polls'] == 0  # Should be decremented
    
    @pytest.mark.asyncio
    async def test_poll_device_now(self, scheduler, mock_db_session_factory):
        """Test manual device polling"""
        session = mock_db_session_factory.return_value
        
        with patch('app.monitoring.scheduler.MonitoringManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.monitor_device.return_value = {'success': True}
            mock_manager_class.return_value = mock_manager
            
            result = await scheduler.poll_device_now(1)
            
            assert result['success'] is True
            assert mock_manager.monitor_device.called
            assert session.close.called
    
    @pytest.mark.asyncio
    async def test_scheduler_statistics_update(self, scheduler, mock_db_session_factory):
        """Test scheduler statistics update"""
        mock_device = Mock()
        mock_device.id = 1
        mock_device.last_polled = None
        
        session = mock_db_session_factory.return_value
        session.query.return_value.filter.return_value.all.return_value = [mock_device]
        
        with patch('app.monitoring.scheduler.MonitoringManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.monitor_device.return_value = {'success': True}
            mock_manager_class.return_value = mock_manager
            
            await scheduler._poll_all_devices()
            
            assert scheduler.stats['total_polls'] == 1
            assert scheduler.stats['successful_polls'] == 1
            assert scheduler.stats['last_poll'] is not None


class TestSchedulerGlobalFunctions:
    """Test global scheduler functions"""
    
    def test_init_scheduler(self):
        """Test scheduler initialization"""
        mock_factory = Mock()
        scheduler = init_scheduler(mock_factory)
        
        assert scheduler is not None
        assert isinstance(scheduler, MonitoringScheduler)
    
    def test_get_scheduler(self):
        """Test get scheduler"""
        mock_factory = Mock()
        init_scheduler(mock_factory)
        
        scheduler = get_scheduler()
        
        assert scheduler is not None
        assert isinstance(scheduler, MonitoringScheduler)
