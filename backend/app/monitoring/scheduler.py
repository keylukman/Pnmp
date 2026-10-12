"""
Monitoring Scheduler
Runs periodic device monitoring tasks
"""
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from .manager import MonitoringManager
from ..models import Device, DeviceCredential, DeviceStatus
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)


class MonitoringScheduler:
    """
    Lightweight async scheduler for device monitoring.
    Runs polling tasks at configured intervals with concurrency control.
    """
    
    def __init__(self, db_session_factory, interval: int = None):
        self.db_session_factory = db_session_factory
        self.running = False
        self.task = None
        self.interval = (interval if interval is not None
                         else settings.MONITORING_INTERVAL_SECONDS)
        # NOTE: the Semaphore must NOT be created in __init__. In Python 3.10+
        # an asyncio primitive binds to the event loop on first use; creating
        # it outside a running loop (e.g. at app startup / lifespan) and later
        # awaiting it inside uvicorn's loop raises "attached to a different
        # loop". Create lazily inside the running loop instead.
        self._semaphore: Optional[asyncio.Semaphore] = None

        # Per-device last poll time (respects each device's polling interval)
        self.last_device_poll: Dict[int, datetime] = {}

        # Monitoring statistics
        self.stats = {
            'total_polls': 0,
            'successful_polls': 0,
            'failed_polls': 0,
            'last_poll': None,
            'active_polls': 0
        }

    @property
    def concurrency_limit(self) -> asyncio.Semaphore:
        """Lazily-created semaphore bound to the current running loop.

        Python 3.10+ deprecation: an asyncio primitive created outside a
        running event loop binds to whichever loop first runs it; creating
        one at import/startup time and awaiting it inside uvicorn's loop can
        raise 'attached to a different loop'. Creating it lazily *inside* the
        running loop avoids that entirely.
        """
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(settings.MONITORING_MAX_CONCURRENCY)
        return self._semaphore
    
    async def start(self):
        """Start the monitoring scheduler (idempotent - no duplicate loops)"""
        if self.running and self.task is not None and not self.task.done():
            logger.warning("Monitoring scheduler already running; ignoring duplicate start")
            return
        
        self.running = True
        logger.info(f"Starting monitoring scheduler with {self.interval}s interval")
        self.task = asyncio.create_task(self._run_loop())
    
    async def stop(self):
        """Stop the monitoring scheduler gracefully"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
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
    
    def _device_interval_seconds(self, device: Device) -> int:
        """Effective polling interval for a device (global default unless overridden)"""
        override = getattr(device, 'polling_interval_seconds', None)
        if override and override > 0:
            return int(override)
        return self.interval
    
    def _is_due(self, device: Device, now: datetime) -> bool:
        """Whether this device is due for polling based on its own interval.

        Uses the persisted ``Device.last_polled`` timestamp when available
        (updated by the monitoring manager on each completed poll and survives
        scheduler restarts), falling back to the in-process map, so a restarted
        scheduler does not immediately re-poll every device.
        """
        last = getattr(device, 'last_polled', None)
        if last is None:
            last = self.last_device_poll.get(device.id)
        if last is None:
            return True  # never polled — poll now to establish a baseline
        # Normalize both sides to naive UTC so arithmetic works whether the
        # driver returned tz-aware (PostgreSQL) or naive (SQLite) datetimes.
        if last.tzinfo is not None:
            last = last.astimezone(timezone.utc).replace(tzinfo=None)
        now_naive = now.astimezone(timezone.utc).replace(tzinfo=None) \
            if isinstance(now, datetime) and now.tzinfo is not None else now
        return (now_naive - last).total_seconds() >= self._device_interval_seconds(device)
    
    async def _poll_all_devices(self):
        """Poll all enabled devices that are due, with concurrency control"""
        db = self.db_session_factory()
        try:
            # Only explicitly enabled devices; maintenance devices are skipped
            devices = db.query(Device).filter(
                Device.monitoring_enabled == True,
                Device.status != DeviceStatus.MAINTENANCE
            ).all()
            
            if not devices:
                logger.debug("No devices to monitor")
                return
            
            # Filter by per-device polling interval (tz-aware clock; _is_due
            # normalizes persisted timestamps to match)
            now = datetime.now(timezone.utc)
            due_devices = [d for d in devices if self._is_due(d, now)]
            if not due_devices:
                logger.debug("No devices due for polling this cycle")
                return
            
            # Poll only devices that have credentials configured.
            # (Devices without credentials are skipped so they do not get
            # spuriously marked DOWN/WARNING by unreachable-SNMP failures.)
            # NOTE: ``c`` rows are Row objects — the attribute is ``device_id``,
            # NOT the table class attribute ``DeviceCredential.device_id``
            # (a Column object, unhashable and never equal to an int id).
            cred_ids = {c.device_id for c in db.query(
                DeviceCredential.device_id).all()}
            ready = [d for d in due_devices if d.id in cred_ids]
            for d in due_devices:
                if d.id not in cred_ids:
                    logger.debug(f"Skipping device {d.id}: no credentials configured")
            
            if not ready:
                logger.debug("No pollable devices (missing credentials)")
                return
            
            logger.info(f"Polling {len(ready)} devices")
            self.stats['last_poll'] = datetime.utcnow()
            for device in ready:
                self.last_device_poll[device.id] = datetime.utcnow()
            
            # Create monitoring manager
            manager = MonitoringManager(db)
            
            # Poll devices concurrently with semaphore limit
            tasks = [
                self._poll_device_with_semaphore(manager, device.id)
                for device in ready
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update statistics
            self.stats['total_polls'] += len(results)
            success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
            failure_count = len(results) - success_count
            
            self.stats['successful_polls'] += success_count
            self.stats['failed_polls'] += failure_count
            
            logger.info(f"Polling complete: {success_count} success, {failure_count} failed")
            
        finally:
            db.close()
    
    async def _poll_device_with_semaphore(self, manager: MonitoringManager, device_id: int):
        """Poll a single device with concurrency control"""
        async with self.concurrency_limit:
            self.stats['active_polls'] += 1
            try:
                result = await manager.monitor_device(device_id)
                return result
            except Exception as e:
                logger.error(f"Error polling device {device_id}: {type(e).__name__}: {e}")
                return {'success': False, 'error': 'MONITORING_ERROR'}
            finally:
                self.stats['active_polls'] -= 1
    
    def get_status(self) -> Dict[str, Any]:
        """Get monitoring scheduler status (reflects actual runtime state)"""
        # If the background task died but the flag is still True, report not running.
        actually_running = self.running and self.task is not None and not self.task.done()
        if self.running and not actually_running:
            self.running = False
        return {
            'running': actually_running,
            'interval': self.interval,
            'max_concurrency': settings.MONITORING_MAX_CONCURRENCY,
            'active_polls': self.stats['active_polls'],
            'total_polls': self.stats['total_polls'],
            'successful_polls': self.stats['successful_polls'],
            'failed_polls': self.stats['failed_polls'],
            'last_poll': self.stats['last_poll'].isoformat() if self.stats['last_poll'] else None
        }
    
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
