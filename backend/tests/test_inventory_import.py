"""
PNMP Milestone 1 — Inventory import/export tests

Covers: valid imports, missing values, malformed IPs, unresolved "ISP"
addresses, duplicate IPs (in-file and in-DB), repeated names, database
conflicts, transactional rollback, unauthorized access (RBAC), credential
redaction, and CSV export from actual records.

All workbooks are generated in-memory; no live devices or production data are
touched. The workbook used here mirrors the agreed column layout of
"perangkat network(1).xlsx"; the real file must be validated on the user's
machine before importing into PostgreSQL.
"""
import io
import json

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from app.core.database import Base
from app.models import (
    Device, DeviceCredential, Site, User, UserRole, DeviceRole,
    DeviceStatus, MonitoringMethod, AuditLog,
)
from app.services import inventory_import as inv


# ---------------------------------------------------------------- helpers

COLS = ["No", "Nama Perangkat", "Lokasi", "Fungsi", "Kondisi",
        "Merk", "Type", "Versi OS", "EOL/EOSL", "IP Address"]


def make_xlsx(rows, columns=None):
    """Build an xlsx in memory. rows = list of lists (no header)."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(columns or COLS)
    for r in rows:
        ws.append(r)
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


GOOD_ROW = [1, "Switch Core 1 ", "Gedung PSSN", "Core Switch L3", "Baik",
            "aruba", "CX 6200F 24G", "ACL-CX 10.13", "", "192.168.10.1"]


@pytest.fixture()
def db_engine(tmp_path):
    """File-backed SQLite shared across the test session and TestClient threads."""
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        f"sqlite:///{tmp_path/'test.db'}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def temp_db(db_engine):
    """Route every SessionLocal() call in the process to the temporary test DB.

    inventory_import.commit_import performs `from ..core.database import
    SessionLocal` at CALL time, so patching the attribute on the
    app.core.database MODULE (not just its original definition site) correctly
    rebinds the service's own session creation. The API request session comes
    from the FastAPI get_db dependency override installed by _build_client —
    both point at the same file-backed SQLite engine, never PostgreSQL.
    """
    maker = sessionmaker(bind=db_engine)

    with patch("app.core.database.SessionLocal", maker):
        yield maker()


def _make_session(db_engine):
    return sessionmaker(bind=db_engine)


def _build_client(role: str, db_engine):
    """FastAPI TestClient whose get_current_user resolves the REAL persisted user.

    Two session paths must be routed to the temporary database:
      1. Request handlers -> via the FastAPI get_db dependency override
         (the application's established testing pattern).
      2. inventory_import.commit_import/_annotate_db_conflicts -> these perform
         `from ..core.database import SessionLocal` at CALL time, so we patch
         the attribute on the app.core.database MODULE for the entire lifetime
         of this client. Without this, the commit step would open a real
         PostgreSQL session (the exact defect behind the previous failure).

    The returned client restores the SessionLocal patch and clears all
    dependency overrides when closed (pytest fixtures are function-scoped, so
    no state leaks between tests).
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api.v1 import devices as devices_api
    from app.core.deps import get_current_user
    from app.core.database import get_db

    maker = sessionmaker(bind=db_engine)
    s = maker()
    user = User(username=f"{role}1", email=f"{role}@x.y", hashed_password="x",
                full_name=role, role=UserRole(role), is_active=True)
    s.add(user); s.commit(); s.refresh(user); uid = user.id; s.close()

    def _current_user():
        db = maker()
        try:
            return db.get(User, uid)
        finally:
            db.close()

    app = FastAPI()
    app.include_router(devices_api.router, prefix="/api/v1")

    def _get_db():
        db = maker()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_db] = _get_db

    # Patch SessionLocal at the module reference the SERVICE imports from,
    # active for every request made through this client.
    patcher = patch("app.core.database.SessionLocal", maker)
    patcher.start()

    client = TestClient(app)
    original_close = client.close

    def close():
        patcher.stop()
        app.dependency_overrides.clear()
        original_close()

    client.close = close  # type: ignore[method-assign]
    return client, user


def row_of(preview, idx=0):
    return preview.rows[idx]


# ---------------------------------------------------------------- unit: validation & mapping

class TestValidation:
    def test_valid_row_normalized(self, temp_db):
        pv = inv.parse_workbook(make_xlsx([GOOD_ROW]), "test.xlsx")
        assert pv.total_rows == 1 and pv.valid_count == 1 and pv.invalid_count == 0
        r = pv.rows[0]
        assert r.name == "Switch Core 1"          # whitespace normalized
        assert r.vendor == "Aruba"                # alias normalized
        assert r.management_ip == "192.168.10.1"
        assert r.device_role == DeviceRole.CORE_SWITCH.value
        assert r.site_name == "Gedung PSSN"
        # firmware only when the workbook actually provides it
        assert r.base_payload()["firmware_version"] == "ACL-CX 10.13"

    def test_missing_required_values(self, temp_db):
        bad = [2, "", "", "", "", "", "", "", "", ""]
        pv = inv.parse_workbook(make_xlsx([bad]), "t.xlsx")
        assert pv.invalid_count == 1
        errs = " | ".join(pv.rows[0].errors)
        assert "Nama Perangkat" in errs and "Lokasi" in errs
        assert "Merk" in errs and "IP Address is required" in errs

    def test_malformed_ip_invalid(self, temp_db):
        r = list(GOOD_ROW); r[9] = "192.168.1300.999"
        pv = inv.parse_workbook(make_xlsx([r]), "t.xlsx")
        assert pv.invalid_count == 1
        assert "not a valid IP address" in pv.rows[0].errors[0]

    def test_hostname_not_accepted_at_import(self, temp_db):
        """Workbook policy: management addresses must be real IPs; hostnames
        are unresolved values (the monitoring engine addresses devices by IP)."""
        r = list(GOOD_ROW); r[9] = "sw-core-01.local"
        pv = inv.parse_workbook(make_xlsx([r]), "t.xlsx")
        assert pv.invalid_count == 1
        assert "Unresolved management address" in pv.rows[0].errors[0]
        assert r[9] == pv.rows[0].ip_raw  # source value preserved for review

    def test_ipv4_cidr_normalized_and_ipv6_accepted(self, temp_db):
        r = list(GOOD_ROW); r[9] = "192.168.10.5/24"
        r2 = list(GOOD_ROW); r2[0] = 2; r2[1] = "v6 GW"; r2[9] = "fe80::1"
        pv = inv.parse_workbook(make_xlsx([r, r2]), "t.xlsx")
        assert pv.invalid_count == 0
        assert pv.rows[0].management_ip == "192.168.10.5"   # prefix not stored
        assert pv.rows[1].management_ip == "fe80::1"

    def test_isp_placeholder_flagged_not_fabricated(self, temp_db):
        """The two 'Cloud Core Router' rows whose IP value is 'ISP' must be
        reported INVALID/unresolved — never converted into a fake address."""
        rows = [[1, "Cloud Core Router", "Gateway", "Router ISP 1", "Baik",
                 "mikrotik", "CCR2004", "", "", "ISP"],
                [2, "Cloud Core Router", "Gateway", "Router ISP 2", "Baik",
                 "mikrotik", "CCR2004", "", "", "ISP"]]
        pv = inv.parse_workbook(make_xlsx(rows), "t.xlsx")
        assert pv.invalid_count == 2
        for r in pv.rows:
            assert r.management_ip is None
            assert "Unresolved management address 'ISP'" in r.errors[0]
            # source information preserved for manual review:
            assert r.ip_raw == "ISP" and r.name == "Cloud Core Router"

    def test_duplicate_ip_in_file_flagged(self, temp_db):
        # GOOD_ROW and r2 share the same IP (192.168.10.1) -> r2 is a duplicate;
        # dup shares it as well -> THREE rows with one address, TWO duplicates.
        r2 = list(GOOD_ROW); r2[0] = 2; r2[1] = "Switch Core 2"
        dup = list(GOOD_ROW); dup[0] = 3; dup[1] = "Switch Dup"
        pv = inv.parse_workbook(make_xlsx([GOOD_ROW, r2, dup]), "t.xlsx")
        assert pv.duplicate_in_file_count == 2
        assert row_of(pv, 0).duplicate_of_row is None            # first wins
        assert row_of(pv, 1).duplicate_of_row == pv.rows[0].row_no
        assert row_of(pv, 2).duplicate_of_row == pv.rows[0].row_no
        assert any("Duplicate IP in file" in w for w in row_of(pv, 2).warnings)

    def test_unique_ips_not_flagged_as_duplicates(self, temp_db):
        a = list(GOOD_ROW); a[0] = 1; a[9] = "10.0.0.1"
        b = list(GOOD_ROW); b[0] = 2; b[1] = "SW B"; b[9] = "10.0.0.2"
        c = list(GOOD_ROW); c[0] = 3; c[1] = "SW C"; c[9] = "10.0.0.3"
        pv = inv.parse_workbook(make_xlsx([a, b, c]), "t.xlsx")
        assert pv.duplicate_in_file_count == 0
        assert all(r.duplicate_of_row is None for r in pv.rows)

    def test_repeated_names_allowed_but_reviewed(self, temp_db):
        a = list(GOOD_ROW); a[0] = 1; a[1] = "Access Point"; a[9] = "10.0.0.1"
        b = list(GOOD_ROW); b[0] = 2; b[1] = "Access Point"; b[9] = "10.0.0.2"
        pv = inv.parse_workbook(make_xlsx([a, b]), "t.xlsx")
        assert pv.invalid_count == 0
        assert pv.review_needed_count == 2
        for r in pv.rows:
            assert any("Repeated device name" in w for w in r.warnings)

    def test_existing_db_ip_conflict_flagged(self, db_session, temp_db):
        db_session.add(Device(hostname="pre", display_name="Pre-existing",
                              management_ip="192.168.10.1", vendor="Aruba",
                              device_type="Switch", device_role=DeviceRole.CORE_SWITCH))
        db_session.commit()
        pv = inv.parse_workbook(make_xlsx([GOOD_ROW]), "t.xlsx")
        r = pv.rows[0]
        assert r.db_existing_device_id is not None
        assert any("already registered" in w for w in r.warnings)
        assert pv.existing_in_db_count == 1

    def test_missing_column_rejected(self, temp_db):
        cols = [c for c in COLS if c != "IP Address"]
        rows = [[str(c) for c in GOOD_ROW[:9]]]
        with pytest.raises(ValueError) as e:
            inv.parse_workbook(make_xlsx(rows, cols), "t.xlsx")
        assert "IP Address" in str(e.value)

    def test_vendor_and_role_mapping(self, temp_db):
        rows = [
            [1, "AP 505", "L1", "Wireless Access Point", "Baik", "aruba", "AP-505", "", "", "10.1.1.1"],
            [2, "CCR", "GW", "Cloud Core Router ISP", "Baik", "mikrotik", "CCR2004", "", "", "10.1.1.2"],
            [3, "FG", "DC", "Firewall perimeter", "Baik", "Fortinet", "FortiGate 101F", "", "", "10.1.1.3"],
            [4, "SW", "L2", "Access switch", "Baik", "Cisco", "Catalyst 2960", "", "", "10.1.1.4"],
            [5, "BL", "GW", "Load balancer WAN", "Baik", "Peplink", "Balance 710", "", "", "10.1.1.5"],
        ]
        pv = inv.parse_workbook(make_xlsx(rows), "t.xlsx")
        roles = [r.device_role for r in pv.rows]
        vendors = [r.vendor for r in pv.rows]
        assert roles == [DeviceRole.ACCESS_POINT.value, DeviceRole.ROUTER.value,
                         DeviceRole.FIREWALL.value, DeviceRole.ACCESS_SWITCH.value,
                         DeviceRole.LOAD_BALANCER.value]
        assert vendors == ["Aruba", "MikroTik", "Fortinet", "Cisco", "Peplink"]




def _locations_from_rows(rows):
    """Distinct Lokasi values in a test workbook (approval list for commits)."""
    seen, out = set(), []
    for r in rows:
        loc = str(r[2]).strip()
        if loc and loc not in seen:
            seen.add(loc)
            out.append(loc)
    return out

# ---------------------------------------------------------------- integration: commit & rollback

class TestTransactionalImport:
    def test_commit_inserts_with_honest_defaults(self, temp_db, db_session):
        rows = [GOOD_ROW,
                [2, "Edge SW", "Gedung Akademik", "Access Switch", "Baik",
                 "aruba", "CX 6100", "", "", "192.168.10.2"]]
        pv = inv.parse_workbook(make_xlsx(rows), "t.xlsx", db=db_session)
        # Milestone 1 site policy: new locations import only when explicitly
        # approved by the operator (what the old auto-create did silently).
        res = inv.commit_import(pv, approved_sites=_locations_from_rows(rows))
        assert res.inserted == 2
        d = db_session.query(Device).filter_by(display_name="Switch Core 1").one()
        # registration is NOT proof of reachability / monitoring:
        assert d.status == DeviceStatus.UNKNOWN
        assert d.monitoring_enabled is False
        assert d.monitoring_method == MonitoringMethod.NONE
        assert d.is_demo is False
        # unknown optional fields stay NULL — never fabricated
        assert d.serial_number is None
        assert d.last_seen is None
        # site created inside the same transaction
        site = db_session.query(Site).filter_by(name="Gedung PSSN").one()
        assert d.site_id == site.id

    def test_duplicates_skipped_never_merged(self, temp_db, db_session):
        dup = list(GOOD_ROW); dup[0] = 9; dup[1] = "Copy Cat"   # same IP as GOOD_ROW
        pv = inv.parse_workbook(make_xlsx([GOOD_ROW, dup]), "t.xlsx", db=db_session)
        res = inv.commit_import(pv, approved_sites=_locations_from_rows([GOOD_ROW, dup]))
        assert res.inserted == 1 and res.skipped_duplicates == 1
        assert db_session.query(Device).count() == 1
        assert db_session.query(Device).filter_by(display_name="Copy Cat").first() is None

    def test_second_run_skips_all_db_conflicts(self, temp_db, db_session):
        pv1 = inv.parse_workbook(make_xlsx([GOOD_ROW]), "t.xlsx", db=db_session)
        inv.commit_import(pv1, approved_sites=_locations_from_rows([GOOD_ROW]))
        pv2 = inv.parse_workbook(make_xlsx([GOOD_ROW]), "t.xlsx", db=db_session)
        res = inv.commit_import(pv2, approved_sites=_locations_from_rows([GOOD_ROW]))
        assert res.inserted == 0 and res.skipped_duplicates == 1
        assert db_session.query(Device).count() == 1

    def test_rollback_writes_nothing_on_failure(self, temp_db, db_session):
        rows = [GOOD_ROW,
                [2, "Second", "Site B", "Switch", "Baik", "cisco", "C2960", "", "", "192.168.10.99"]]
        pv = inv.parse_workbook(make_xlsx(rows), "t.xlsx", db=db_session)
        # simulate a DB failure mid-import (e.g. unique violation on second insert)
        import sqlalchemy.orm as orm

        class Boom(Exception):
            pass

        state = {"flushes": 0}
        target = orm.Session.flush

        def failing_flush(self, *a, **k):
            state["flushes"] += 1
            if state["flushes"] >= 2:
                raise Boom("simulated database conflict")
            return target(self, *a, **k)

        with patch.object(orm.Session, "flush", failing_flush):
            with pytest.raises(Boom):
                inv.commit_import(pv, approved_sites=_locations_from_rows(rows))
        # full rollback: neither first nor second device persisted
        assert db_session.query(Device).count() == 0
        assert db_session.query(Site).count() == 0

    def test_no_credentials_created_by_import(self, temp_db, db_session):
        pv = inv.parse_workbook(make_xlsx([GOOD_ROW]), "t.xlsx", db=db_session)
        inv.commit_import(pv, approved_sites=_locations_from_rows([GOOD_ROW]))
        assert db_session.query(DeviceCredential).count() == 0


# ---------------------------------------------------------------- API layer: RBAC + redaction

class TestApiRbac:
    def test_viewer_cannot_import_preview_or_commit(self, db_engine):
        client, user = _build_client("viewer", db_engine)
        files = {"file": ("wb.xlsx", make_xlsx([GOOD_ROW]), "application/octet-stream")}
        assert client.post("/api/v1/devices/import/preview", files=files).status_code == 403
        assert client.post("/api/v1/devices/import", files=files).status_code == 403
        payload = {"hostname": "x", "display_name": "X", "management_ip": "10.0.0.1",
                   "vendor": "Aruba", "device_type": "Switch", "device_role": "access_switch"}
        assert client.post("/api/v1/devices/", json=payload).status_code == 403
        with _make_session(db_engine)() as s:
            assert s.query(Device).count() == 0

    def test_operator_cannot_delete(self, db_engine):
        client, user = _build_client("operator", db_engine)
        maker = _make_session(db_engine)
        s = maker()
        d = Device(hostname="op", display_name="Op", management_ip="10.9.9.9",
                   vendor="Aruba", device_type="Switch", device_role=DeviceRole.ACCESS_SWITCH)
        s.add(d); s.commit(); did = d.id; s.close()
        assert client.delete(f"/api/v1/devices/{did}").status_code == 403
        s = maker(); assert s.query(Device).count() == 1; s.close()

    def test_admin_can_preview_then_commit_and_audit_written(self, db_engine):
        client, user = _build_client("admin", db_engine)
        maker = _make_session(db_engine)
        content = make_xlsx([GOOD_ROW])
        files = {"file": ("wb.xlsx", content, "application/octet-stream")}

        r = client.post("/api/v1/devices/import/preview", files=files)
        assert r.status_code == 200
        body = r.json()
        assert body["mode"] == "preview"
        assert body["summary"]["valid"] == 1
        s = maker(); assert s.query(Device).count() == 0; s.close()   # preview committed nothing

        r = client.post("/api/v1/devices/import", files=files,
                        data={"approved_sites": "Gedung PSSN"})
        assert r.status_code == 200
        assert r.json()["summary"]["inserted"] == 1
        s = maker()
        assert s.query(Device).count() == 1
        audits = s.query(AuditLog).filter_by(action="device_import").all()
        assert len(audits) == 1 and "inserted=1" in audits[0].details
        s.close()

    def test_upload_validation_errors(self, db_engine):
        client, user = _build_client("admin", db_engine)
        maker = _make_session(db_engine)
        r = client.post("/api/v1/devices/import/preview",
                        files={"file": ("notes.txt", b"hello", "text/plain")})
        assert r.status_code == 400
        r = client.post("/api/v1/devices/import/preview",
                        files={"file": ("broken.xlsx", b"not-a-zip", "application/octet-stream")})
        assert r.status_code == 422
        detail = r.json()["detail"].lower()
        for leak in ("traceback", "sqlite", "select", "insert into"):
            assert leak not in detail

    def test_csv_export_uses_actual_records_and_redacts_secrets(self, db_engine):
        client, user = _build_client("admin", db_engine)
        maker = _make_session(db_engine)
        s = maker()
        d = Device(hostname="ex", display_name="Export Me", management_ip="10.7.7.7",
                   vendor="Aruba", device_type="Switch", device_role=DeviceRole.ACCESS_SWITCH,
                   status=DeviceStatus.UNKNOWN)
        s.add(d); s.commit()
        secret = "TopSecretCommunity!"
        enc = __import__("app.core.encryption", fromlist=["credential_encryption"]).credential_encryption.encrypt(secret)
        s.add(DeviceCredential(device_id=d.id, snmp_version="v2c",
                               snmp_community_encrypted=enc, encrypted_password=enc))
        s.commit(); s.close()

        r = client.get("/api/v1/devices/export.csv")
        assert r.status_code == 200
        text = r.text
        assert "Export Me" in text and "10.7.7.7" in text
        assert secret not in text and enc not in text
        lowered = text.lower()
        for forbidden in ("community", "password"):
            assert forbidden not in lowered

class TestHarnessIsolation:
    """Regression guard: the inventory tests must NEVER open a connection to the
    configured PostgreSQL database. app.core.database.engine is bound to
    settings.DATABASE_URL (PostgreSQL by default); any accidental use of
    SessionLocal()/get_db without the overrides installed above would try to
    connect there and fail in this environment. This test proves the harness
    routes both the service-level sessions AND the API request sessions to the
    temporary SQLite engine only.
    """

    def test_no_postgres_connection_from_harness(self, db_engine):
        from app.core import database as database_module

        # The production engine really is PostgreSQL-bound in default config;
        # if that ever changes, the guard below still stands on its own.
        assert str(database_module.engine.url).startswith("postgresql"), \
            "expected default DATABASE_URL to be PostgreSQL for this guard"

        client, user = _build_client("admin", db_engine)
        maker = _make_session(db_engine)
        content = make_xlsx([GOOD_ROW])
        files = {"file": ("wb.xlsx", content, "application/octet-stream")}

        with patch("app.core.database.SessionLocal", maker):
            # preview path uses the overridden get_db dependency
            r = client.post("/api/v1/devices/import/preview", files=files)
            assert r.status_code == 200
            # commit path uses the patched module-level SessionLocal
            r = client.post("/api/v1/devices/import", files=files,
                        data={"approved_sites": "Gedung PSSN"})
            assert r.status_code == 200

        # Everything landed in the temp DB...
        s = maker()
        assert s.query(Device).count() == 1
        assert s.query(AuditLog).filter_by(action="device_import").count() == 1
        s.close()
        # ...and the real PostgreSQL engine was never connected/touched:
        # its pool has no checked-out connections and would have raised an
        # OperationalError (no PG server in the test environment) if any code
        # path had tried to use it.
        assert database_module.engine.pool.checkedout() == 0


class TestSiteMappingPolicy:
    """Milestone 1 Task D: deterministic Lokasi -> site mapping, no auto-create."""

    def test_preview_reports_site_mapping_without_writing(self, db_engine):
        maker = _make_session(db_engine)
        s = maker()
        s.add(Site(name="Gedung PSSN"))
        s.add(Site(name="Kantor A"))
        s.add(Site(name="Kantor B"))
        s.commit()
        rows = [
            GOOD_ROW,  # Lokasi "Gedung PSSN" -> matched existing site
            [2, "Ambiguity SW", "Kantor", "Switch", "Baik", "cisco", "C2960", "", "", "10.9.1.1"],
        ]
        before_devices = s.query(Device).count()
        pv = inv.parse_workbook(make_xlsx(rows), "map.xlsx", db=s)
        by_loc = {e.location: e for e in pv.site_mapping}
        assert by_loc["Gedung PSSN"].status == "matched"
        assert by_loc["Gedung PSSN"].site_id is not None
        assert by_loc["Kantor"].status == "new_pending_approval"
        assert by_loc["Kantor"].row_numbers == [3]  # source row preserved
        # preview NEVER writes devices or sites
        assert s.query(Device).count() == before_devices
        assert s.query(Site).count() == 3
        s.close()

    def test_unapproved_new_location_is_skipped_not_created(self, temp_db, db_session):
        rows = [GOOD_ROW,
                [2, "New Site SW", "Gedung Baru", "Switch", "Baik", "cisco",
                 "C2960", "", "", "192.168.99.1"]]
        pv = inv.parse_workbook(make_xlsx(rows), "t.xlsx", db=db_session)
        res = inv.commit_import(pv, approved_sites=["Gedung Baru"])  # only new one approved
        names = {d.display_name for d in db_session.query(Device).all()}
        # "Gedung PSSN" did NOT match an existing site and was NOT approved:
        assert "Switch Core 1" not in names
        assert "New Site SW" in names
        assert res.inserted == 1 and res.skipped_site_review == 1
        assert db_session.query(Site).filter_by(name="Gedung PSSN").first() is None
        assert db_session.query(Site).filter_by(name="Gedung Baru").first() is not None

    def test_matched_existing_site_needs_no_approval(self, temp_db, db_session):
        s = db_session
        st = Site(name="Gedung PSSN")
        s.add(st); s.commit()
        pv = inv.parse_workbook(make_xlsx([GOOD_ROW]), "t.xlsx", db=s)
        res = inv.commit_import(pv)  # no approvals needed for matched locations
        assert res.inserted == 1
        dev = s.query(Device).one()
        assert dev.site_id == st.id
        # exactly one site still — no duplicate created
        assert s.query(Site).count() == 1

    def test_ambiguous_location_never_guesses(self, temp_db, db_session):
        s = db_session
        # two distinct sites whose normalized names collide case-insensitively
        s.add_all([Site(name="kantor pusat"), Site(name="Kantor Pusat ")])
        s.commit()
        pv = inv.parse_workbook(
            make_xlsx([[2, "Amb SW", "Kantor Pusat", "Switch", "Baik", "cisco",
                        "C2960", "", "", "10.9.9.9"]]), "t.xlsx", db=s)
        entry = next(e for e in pv.site_mapping if e.location == "Kantor Pusat")
        assert entry.status == "ambiguous"
        res = inv.commit_import(pv, approved_sites=["Kantor Pusat"])
        # approval cannot resolve ambiguity — row stays skipped for manual review
        assert res.inserted == 0 and res.skipped_site_review == 1
        assert s.query(Device).count() == 0


class TestApiRbac2:
    def test_update_ip_resets_stale_reachability(self, db_engine):
        from datetime import datetime
        client, user = _build_client("admin", db_engine)
        maker = _make_session(db_engine)
        s = maker()
        d = Device(hostname="mv", display_name="Move Me", management_ip="10.1.1.1",
                   vendor="Aruba", device_type="Switch", device_role=DeviceRole.ACCESS_SWITCH,
                   status=DeviceStatus.UP, last_seen=datetime.utcnow(), failure_count=0)
        s.add(d); s.commit(); did = d.id; s.close()
        r = client.put(f"/api/v1/devices/{did}", json={"management_ip": "10.2.2.2"})
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "unknown"
        assert body["last_seen"] is None
