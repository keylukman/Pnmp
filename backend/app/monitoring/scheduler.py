"""
Monitoring Scheduler
Runs periodic device monitoring tasks
"""
import asyncio
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from .manager import MonitoringManager
from ..models import Device, DeviceStatus
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)


class MonitoringScheduler:
    """
    Lightweight async scheduler for device monitoring.
    Runs polling tasks at configured intervals.
    """
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.running = False
        self.task = None
        self.interval = settings.MONITORING_INTERVAL_SECONDS
    
    async def start(self):
        """Start the monitoring scheduler"""
        if self.running:
            logger.warning("Monitoring scheduler already running")
            return
        
        self.running = True
        logger.info(f"Starting monitoring scheduler with {self.interval}s interval")
        self.task = asyncio.create_task(self._run_loop())
    
    async def stop(self):
        """Stop the monitoring scheduler"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Monitoring scheduler stopped")
    
    async def _run_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                await self._poll_all_devices()
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait before retry
    
    async def _poll_all_devices(self):
        """Poll all enabled devices"""
        db = self.db_session_factory()
        try:
            # Get all devices with monitoring enabled
            devices = db.query(Device).filter(
                Device.monitoring_enabled == True,
                Device.status != DeviceStatus.MAINTENANCE
            ).all()
            
            if not devices:
                logger.debug("No devices to monitor")
                return
            
            logger.info(f"Polling {len(devices)} devices")
            
            # Create monitoring manager
            manager = MonitoringManager(db)
            
            # Poll devices concurrently with semaphore limit
            tasks = [
                self._poll_device_safe(manager, device.id)
                for device in devices
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
            failure_count = len(results) - success_count
            
            logger.info(f"Polling complete: {success_count} success, {failure_count} failed")
            
        finally:
            db.close()
    
    async def _poll_device_safe(self, manager: MonitoringManager, device_id: int):
        """Safely poll a single device"""
        try:
            result = await manager.monitor_device(device_id)
            return result
        except Exception as e:
            logger.error(f"Error polling device {device_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def poll_device_now(self, device_id: int) -> dict:
        """
        Manually trigger polling for a specific device.
        Used by test-connection endpoint.
        """
        db = self.db_session_factory()
        try:
            manager = MonitoringManager(db)
            result = await manager.monitor_device(device_id)
            return result
        finally:
            db.close()


# Global scheduler instance
_scheduler = None

def get_scheduler():
    """Get global scheduler instance"""
    global _scheduler
    return _scheduler

def init_scheduler(db_session_factory):
    """Initialize global scheduler"""
    global _scheduler
    _scheduler = MonitoringScheduler(db_session_factory)
    return _scheduler
