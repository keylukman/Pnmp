# PNMP — Milestone 0 Repository Audit

Date: 2026-10-21 (audit executed in the Linux-based analysis sandbox; target runtime remains native Windows 11)
Branch audited: `main` @ `facb6bf5` ("Merge pull request #19 … monitoring-engine-verification-9090c")

## 1. What exists (verified, not assumed)

### Backend (`backend/`) — FastAPI modular monolith, ~3,400 LOC of application code
| Area | Status | Evidence |
|---|---|---|
| App entry / lifespan | Working | `app/main.py`; full startup + graceful shutdown executed via TestClient smoke test (see §3) |
| Config | Working | `app/core/config.py`, `.env.example` complete (DB, JWT, encryption key, monitoring, SNMP, Aruba TLS, Zabbix, logging) |
| DB layer | Working | SQLAlchemy 2.x + psycopg3; Alembic with a linear 2-revision chain: `20261009_0001` → `20261012_0002_metrics_null_semantics` (head) |
| Models | Working | users, sites, devices, device_credentials, device_interfaces, alerts, event_logs, audit_logs, topology_links, device_metrics, interface_metrics |
| Auth / RBAC | Implemented | JWT login, role enum (Administrator / Network Operator / Read-Only Viewer), protected endpoints verified to return **401 without token** |
| Device CRUD | Implemented | List w/ filters+pagination, create/update/delete, test-connection, credential store/retrieve (redacted responses), interfaces listing — 37 routes under `/api/v1` confirmed at runtime |
| Credential security | Implemented | Fernet encryption; production refuses to start without `PNMP_ENCRYPTION_KEY`; dev fallback key file is gitignored; regression tests assert no secret fields are ever returned |
| Monitoring engine | Implemented | Async scheduler with bounded concurrency (lazy semaphore for Python 3.12 loop-binding), per-device intervals, skip disabled/maintenance/no-credential devices, failure threshold before DOWN, alert dedup + auto-resolve, NULL-vs-zero metric semantics, counter-reset handling |
| Adapters | Partial | GenericSNMP (pysnmp) and ArubaCX REST exist; registry raises explicitly for unimplemented methods (no silent fallback). WLC/Cisco/MikroTik/FortiGate/Peplink/Zabbix adapters **not yet implemented** |
| Zabbix integration API | Scaffolded | `app/api/v1/integrations.py` (status/test/hosts/problems); optional — core app starts without it |
| Tests | Passing | `pytest`: **36 passed** (unit + Step-8 regression incl. NULL semantics, counter resets, alert dedup, scheduler lifecycle, credential redaction, ping-injection guard) |
| Seed | Working (needs DB) | `seed.py` creates admin/neteng1; uses `create_all`, no destructive drops |

### Frontend (repo root, `src/`) — React 18 + TypeScript + Vite + Tailwind 4 + ECharts
- Pages present: Dashboard, Devices (+detail), Interfaces, Alerts, Topology, WAN, Reports, Sites, Users, Settings, Login.
- Zustand stores + centralized API client (`src/services/api.ts`).
- `npm run build` succeeds (only a chunk-size warning).
- ⚠️ Contains an automatic **"demo mode" fallback** that renders fabricated local data when the backend is unreachable (README even documents "Login: any user / any password"). This violates the "no fake data presented as live" rule and must be gated/labeled in Milestone 1.
- ⚠️ Stack deviation: master prompt requests **Vue 3**; existing project is **React**. Per working rules ("keep existing layout if reasonable", "preserve working features"), recommendation is to keep React unless the user explicitly orders a rewrite.

### Scripts & docs
- Only one PowerShell script existed (`setup.ps1`, frontend-only). No scripts for venv, migration, health check, start/stop, or PostgreSQL verification.
- `perangkat network.xlsx` (inventory source workbook): **NOT PRESENT in the repository.** Import feature must not proceed without it.

## 2. Environment caveat
This audit sandbox has no PostgreSQL server and is not Windows. Database connectivity, `alembic upgrade head` against a real cluster, and uvicorn-on-Windows were therefore **not** executed here; they must be run by the user on `F:\pnmp` (commands in §4). All other verifications below were actually executed.

## 3. Verification performed (actual results)
1. `pip install -r requirements.txt` → success, pinned versions resolved cleanly.
2. `python -c "from app.main import app"` → clean import.
3. `pytest tests/ -v` → **36 passed**, 0 failed (~2 s; only `utcnow()` DeprecationWarnings).
4. Full-lifespan smoke test (in-memory SQLite substituted for PostgreSQL): startup OK, `/health` → `{status: healthy, database: connected, monitoring_worker: running}`, `/docs` → 200, scheduler start→poll-cycle→graceful stop OK, 37 API routes registered, `GET /api/v1/devices/` without token → **401**.
5. Frontend `npm run build` → success.
6. Alembic revision chain inspected: single linear head, no branch conflicts.

## 4. Foundation issues found & disposition
| # | Issue | Severity | Action taken in M0 |
|---|---|---|---|
| F1 | No Windows PowerShell operational scripts | Medium | **Fixed**: added `scripts/check-env.ps1`, `setup-backend.ps1`, `check-db.ps1`, `migrate.ps1`, `start-backend.ps1`, `start-frontend.ps1`, `health-check.ps1`, `run-tests.ps1` |
| F2 | Inventory workbook missing from repo | Blocker for M1 import | **Reported, not invented** — user must supply `perangkat network.xlsx` |
| F3 | Frontend demo-mode fake data | Medium | Deferred to M1 (label/gate removal) — no working feature deleted now |
| F4 | `Base.metadata.create_all` at startup alongside Alembic | Low | Kept (dev convenience, non-destructive); documented that Alembic is authoritative |
| F5 | Vue vs React stack deviation | Decision needed | Kept React; awaiting user approval either way |
| F6 | Missing vendor adapters (Cisco, MikroTik, FortiGate, Peplink, WLC, Zabbix provider) | Planned gaps | Not built prematurely; matches milestone plan (M5–M7) |

No other essential foundation defects were found. No existing project files modified beyond adding `scripts/` and this document.

## 5. Commands the user must run on Windows (PowerShell, from `F:\pnmp`)
```powershell
.\scripts\check-env.ps1        # verify Node/Python/PostgreSQL presence
.\scripts\setup-backend.ps1    # create .venv, install pinned deps, copy .env.example -> .env
# edit backend\.env (DATABASE_URL, JWT_SECRET_KEY, PNMP_ENCRYPTION_KEY)
.\scripts\check-db.ps1         # verify PostgreSQL service, database and role
.\scripts\migrate.ps1          # alembic upgrade head
cd backend; .\.venv\Scripts\Activate.ps1; python seed.py   # create admin user
.\scripts\start-backend.ps1    # uvicorn app.main:app --reload  (terminal 1)
.\scripts\start-frontend.ps1   # npm run dev                    (terminal 2)
.\scripts\health-check.ps1     # GET /health
.\scripts\run-tests.ps1        # pytest
```

## 6. Prioritized plan after Milestone 0
1. **M1 Inventory & DB** — needs the Excel workbook; add import preview/validation/duplicate detection + CSV export; gate/remove frontend demo data; add backend integration tests over SQLite fixtures.
2. **M2 hardening** — verify scheduler against real PostgreSQL; retention job for metrics; stale-data flag surfacing in API.
3. **M3 Interfaces** — rate/utilization history endpoints + charts from real samples.
4. **M4 Dashboard/Alerts** — replace remaining placeholder panels with real aggregate queries.
5. **M5 Aruba CX** capability detection & diagnostics; then M6 WLC/Zabbix, M7 topology/backups, M8 security release review.

**Status: Milestone 0 complete. Awaiting user review and the inventory workbook before Milestone 1.**
