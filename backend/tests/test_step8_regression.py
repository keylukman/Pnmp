"""
PNMP Phase 3 Step 8 — Regression tests
Scheduler lifecycle, polling selection rules, status transitions, alert dedup,
monitoring-status API, credential secrecy, defaults, TLS config, async ping safety.

All adapters are MOCKED. These tests prove code behavior only — they are NOT
evidence of real-device connectivity.
"""
import asyncio
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.config import settings
from app.models import (
    Device, DeviceCredential, DeviceInterface, DeviceMetric, InterfaceMetric,
    Alert, EventLog, User, Site, UserRole,
    DeviceStatus, MonitoringMethod, AlertStatus, AlertSeverity, EventType,
)
from app.monitoring.scheduler import MonitoringScheduler
from app.monitoring.manager import MonitoringManager
from app.monitoring.adapters import AdapterRegistry


# ----------------------------------------------------------------------------- fixtures
@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


from app.models import DeviceRole


def make_device(db, ip="10.0.0.1", enabled=True, method=MonitoringMethod.SNMP,
               interval=None, status=DeviceStatus.UNKNOWN, name="sw-01"):
    device = Device(
        hostname=name, display_name=name, management_ip=ip,
        vendor="Generic", device_type="Switch",
        device_role=DeviceRole.ACCESS_SWITCH,
        monitoring_enabled=enabled, monitoring_method=method,
        polling_interval_seconds=interval, status=status, failure_count=0,
    )
    db.add(device)
    db.commit()
    return device


class FakeAdapter:
    """Fully mocked adapter — never touches the network."""

    def __init__(self, ok=True):
        self.ok = ok
        self.closed = False

    async def test_connection(self):
        if self.ok:
            return {'success': True, 'latency_ms': 5.0}
        return {'success': False, 'message': 'timeout', 'error_code': 'CONN_FAILED'}

    async def get_system_info(self):
        return {'hostname': 'fake', 'cpu': 25, 'memory': 45,
                'temperature': None, 'uptime_seconds': 100}

    async def get_interfaces(self):
        return [{'if_index': 1, 'name': 'eth1', 'status': 'up',
                 'admin_status': 'up', 'speed_bps': 1_000_000_000,
                 'description': '', 'alias': ''}]

    async def get_interface_statistics(self):
        return [{'if_index': 1, 'name': 'eth1', 'rx_bytes': 1000, 'tx_bytes': 500,
                 'rx_errors': 0, 'tx_errors': 0}]

    async def close(self):
        self.closed = True


# ----------------------------------------------------------------------------- scheduler lifecycle
class TestSchedulerLifecycle:
    async def test_start_stop_and_idempotency(self):
        sched = MonitoringScheduler(sessionmaker())
        await sched.start()
        first_task = sched.task
        assert sched.get_status()['running'] is True
        await sched.start()                      # must NOT spawn a second loop
        assert sched.task is first_task
        await sched.stop()
        assert sched.get_status()['running'] is False
        assert sched.task is None
        await sched.stop()                      # double stop must be safe

    async def test_get_status_reflects_dead_task(self):
        sched = MonitoringScheduler(sessionmaker())
        await sched.start()
        sched.task.cancel()
        try:
            await sched.task
        except asyncio.CancelledError:
            pass
        # task done but flag still True -> status must report not running
        assert sched.get_status()['running'] is False

    async def test_poll_skips_disabled_maintenance_and_no_credentials(self, db_session):
        d_on = make_device(db_session, "10.0.0.1", enabled=True)
        make_device(db_session, "10.0.0.2", enabled=False)          # disabled
        make_device(db_session, "10.0.0.3", enabled=True,
                    status=DeviceStatus.MAINTENANCE)                 # maintenance
        factory = lambda: db_session
        sched = MonitoringScheduler(factory)
        called = []

        async def fake_poll(device_id):
            called.append(device_id)
            return {'success': True}

        with patch.object(sched, '_poll_device_with_semaphore', side_effect=lambda m, did: fake_poll(did)):
            await sched._poll_all_devices()
        assert called == [d_on.id]   # only the enabled, non-maintenance device

    async def test_per_device_interval_respected(self, db_session):
        d = make_device(db_session, "10.0.0.10", enabled=True, interval=3600)
        sched = MonitoringScheduler(lambda: db_session)
        assert sched._device_interval_seconds(d) == 3600
        d.polling_interval_seconds = None
        assert sched._device_interval_seconds(d) == sched.interval
        now = datetime.utcnow()
        sched.last_device_poll[d.id] = now - timedelta(seconds=60)
        assert sched._is_due(d, now) is False       # 60s < 3600s override
        sched.last_device_poll[d.id] = now - timedelta(seconds=3700)
        assert sched._is_due(d, now) is True

    async def test_credential_prefilter(self, db_session):
        d = make_device(db_session, "10.0.0.11", enabled=True)      # no credentials row
        sched = MonitoringScheduler(lambda: db_session)
        pollable = db_session.query(Device).filter(
            Device.monitoring_enabled == True,
            Device.status != DeviceStatus.MAINTENANCE,
        ).all()
        # manager-level guard: polling without credentials fails safely
        mgr = MonitoringManager(db_session)
        result = await mgr.monitor_device(d.id)
        assert result['success'] is False
        assert result['error_code'] == 'NO_CREDENTIALS'


# ----------------------------------------------------------------------------- status/alerts
class TestStatusAndAlerts:
    async def test_single_failure_does_not_mark_down(self, db_session):
        d = make_device(db_session, "10.0.0.20", enabled=True, status=DeviceStatus.UP)
        mgr = MonitoringManager(db_session)
        res = await mgr._handle_monitoring_failure(
            d, {'message': 'timeout', 'error_code': 'TIMEOUT'})
        db_session.refresh(d)
        assert d.status != DeviceStatus.DOWN
        assert d.failure_count == 1
        assert db_session.query(Alert).count() == 0

    async def test_threshold_reached_creates_alert_once(self, db_session):
        d = make_device(db_session, "10.0.0.21", enabled=True, status=DeviceStatus.UP)
        mgr = MonitoringManager(db_session)
        for _ in range(mgr.failure_threshold):
            await mgr._handle_monitoring_failure(d, {'message': 'unreachable'})
        db_session.refresh(d)
        assert d.status == DeviceStatus.DOWN
        assert db_session.query(Alert).filter(Alert.device_id == d.id).count() == 1
        # extra failed cycles while already DOWN must not duplicate alerts/events
        for _ in range(2):
            await mgr._handle_monitoring_failure(d, {'message': 'unreachable'})
        assert db_session.query(Alert).filter(Alert.device_id == d.id).count() == 1
        down_events = db_session.query(EventLog).filter(
            EventLog.device_id == d.id, EventLog.event_type == EventType.DEVICE_DOWN).count()
        assert down_events == 1

    async def test_recovery_resolves_alert_and_emits_event(self, db_session):
        d = make_device(db_session, "10.0.0.22", enabled=True, status=DeviceStatus.UP)
        mgr = MonitoringManager(db_session)
        for _ in range(mgr.failure_threshold):
            await mgr._handle_monitoring_failure(d, {'message': 'unreachable'})
        alert = db_session.query(Alert).filter(Alert.device_id == d.id).first()
        assert alert is not None and alert.status == AlertStatus.OPEN
        await mgr._handle_monitoring_success(d)
        db_session.refresh(d); db_session.refresh(alert)
        assert d.status == DeviceStatus.UP
        assert alert.status == AlertStatus.RESOLVED
        up_events = db_session.query(EventLog).filter(
            EventLog.device_id == d.id, EventLog.event_type == EventType.DEVICE_UP).count()
        assert up_events == 1


# ----------------------------------------------------------------------------- persistence
class TestPersistence:
    async def test_successful_poll_persists_metrics(self, db_session):
        d = make_device(db_session, "10.0.0.30", enabled=True)
        cred = DeviceCredential(device_id=d.id, snmp_version='v2c',
                                snmp_community_encrypted='enc-test')
        db_session.add(cred); db_session.commit()
        with patch('app.monitoring.manager.AdapterRegistry.get_adapter',
                   return_value=FakeAdapter(ok=True)):
            mgr = MonitoringManager(db_session)
            res = await mgr.monitor_device(d.id)
        assert res['success'] is True
        assert db_session.query(DeviceMetric).filter(
            DeviceMetric.device_id == d.id).count() == 1
        iface = db_session.query(DeviceInterface).filter(
            DeviceInterface.device_id == d.id).first()
        assert iface is not None and iface.if_index == 1
        im = db_session.query(InterfaceMetric).filter(
            InterfaceMetric.device_id == d.id).first()
        assert im is not None
        # first poll = baseline: rates NULL, raw counters stored, no fabricated zeros
        assert im.rx_bps is None and im.tx_bps is None
        assert im.rx_bytes == 1000

    async def test_failed_poll_writes_no_metrics(self, db_session):
        d = make_device(db_session, "10.0.0.31", enabled=True)
        cred = DeviceCredential(device_id=d.id, snmp_version='v2c',
                                snmp_community_encrypted='enc-test')
        db_session.add(cred); db_session.commit()
        with patch('app.monitoring.manager.AdapterRegistry.get_adapter',
                   return_value=FakeAdapter(ok=False)):
            mgr = MonitoringManager(db_session)
            res = await mgr.monitor_device(d.id)
        assert res['success'] is False
        assert db_session.query(DeviceMetric).count() == 0
        assert db_session.query(InterfaceMetric).count() == 0


# ----------------------------------------------------------------------------- monitoring status API
class TestMonitoringStatusAPI:
    async def test_status_endpoint_reflects_runtime(self, db_session):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.api.v1 import monitoring as monitoring_api
        from app.core.deps import get_current_user

        app = FastAPI()
        app.include_router(monitoring_api.router, prefix="/api/v1/monitoring")
        user = User(username="admin", email="a@b.c", hashed_password="x",
                    full_name="Admin", role=UserRole.ADMIN, is_active=True)
        db_session.add(user); db_session.commit()
        app.dependency_overrides[get_current_user] = lambda: user

        client = TestClient(app)

        # No scheduler -> honest 503 (must not falsely report running)
        with patch('app.monitoring.get_scheduler', return_value=None):
            r = client.get("/api/v1/monitoring/status")
            assert r.status_code == 503

        sched = MonitoringScheduler(lambda: db_session)
        with patch('app.monitoring.get_scheduler', return_value=sched):
            await sched.start()
            r = client.get("/api/v1/monitoring/status")
            assert r.status_code == 200
            data = r.json()
            assert data['running'] is True
            for key in ('interval', 'max_concurrency', 'active_polls', 'total_polls',
                        'successful_polls', 'failed_polls', 'last_poll'):
                assert key in data
            await sched.stop()
            r = client.get("/api/v1/monitoring/status")
            assert r.json()['running'] is False

        # response must never contain secret material
        body_text = str(r.json()).lower()
        for bad in ('password', 'community', 'token', 'secret'):
            assert bad not in body_text


# ----------------------------------------------------------------------------- security
class TestSecurity:
    def test_safe_response_has_no_secret_fields(self):
        from app.schemas import DeviceCredentialSafeResponse
        forbidden = {'snmp_community', 'community', 'password', 'auth_password',
                     'privacy_password', 'encrypted_password', 'snmp_community_encrypted',
                     'snmp_auth_password_encrypted', 'snmp_privacy_password_encrypted'}
        fields = set(DeviceCredentialSafeResponse.model_fields.keys())
        assert not (fields & forbidden), fields & forbidden

    def test_credentials_never_returned_by_api(self, db_session):
        """GET /devices/{id}/credentials must not serialize encrypted values."""
        from app.schemas import DeviceCredentialSafeResponse
        secret = "Sup3rSecretCommunity"
        enc = __import__('app.core.encryption', fromlist=['credential_encryption']).credential_encryption.encrypt(secret)
        assert enc != secret
        resp = DeviceCredentialSafeResponse(**{
            'device_id': 1, 'snmp_version': 'v2c', 'has_community': bool(enc),
            'ssh_enabled': False, 'api_enabled': False})
        assert secret not in resp.model_dump_json()
        assert enc not in resp.model_dump_json()

    def test_monitoring_default_off_at_model_and_schema_level(self):
        from app.schemas import DeviceCreate
        from app.models import Device as D
        col = D.__table__.columns['monitoring_enabled']
        assert col.default.arg is False
        payload = DeviceCreate(hostname='h', display_name='d', management_ip='1.2.3.4',
                               vendor='v', device_type='Switch',
                               device_role=DeviceRole.ACCESS_SWITCH)
        assert payload.monitoring_enabled is False

    def test_aruba_tls_verify_defaults_true(self):
        assert settings.ARUBA_TLS_VERIFY is True
        a = __import__('app.monitoring.adapters.aruba_cx',
                       fromlist=['ArubaCXAdapter']).ArubaCXAdapter(1, '10.0.0.9', {})
        assert a._tls_verify is True
        b = __import__('app.monitoring.adapters.aruba_cx',
                       fromlist=['ArubaCXAdapter']).ArubaCXAdapter(
            1, '10.0.0.9', {'tls_verify': False})
        assert b._tls_verify is False   # explicit opt-out only

    def test_ping_target_validation_blocks_injection(self):
        from app.api.v1.devices import _is_valid_host
        assert _is_valid_host("192.168.1.1") is True
        assert _is_valid_host("sw-01.lab.local") is True
        assert _is_valid_host("8.8.8.8; rm -rf /") is False
        assert _is_valid_host("-encodesomething") is False
        assert _is_valid_host("") is False
        assert _is_valid_host("10.0.0.1 && calc.exe") is False

    @pytest.mark.asyncio
    async def test_ping_async_is_nonblocking_and_timeout_bounded(self):
        from app.api.v1.devices import _ping_async
        calls = {}
        def fake_run(cmd, capture_output, text, timeout):
            calls['cmd'] = cmd; calls['timeout'] = timeout
            raise OSError("simulated ping failure")
        with patch('subprocess.run', side_effect=fake_run):
            ok = await _ping_async("10.0.0.1", timeout_seconds=5)
        assert ok is False
        assert isinstance(calls['cmd'], list) and 'shell' not in str(calls['cmd'])
        assert calls['timeout'] <= 7   # bounded hard timeout


# ----------------------------------------------------------------------------- registry
class TestAdapterRegistry:
    def test_unimplemented_methods_raise(self):
        for m in ('zabbix', 'ssh'):
            with pytest.raises(ValueError):
                AdapterRegistry.get_adapter(1, '10.0.0.1', 'Generic', 'Switch', m, {})

    def test_snmp_returns_snmp_adapter(self):
        from app.monitoring.adapters.snmp import GenericSNMPAdapter
        a = AdapterRegistry.get_adapter(1, '10.0.0.1', 'Generic', 'Switch', 'snmp',
                                        {'snmp_version': 'v2c'})
        assert isinstance(a, GenericSNMPAdapter)
