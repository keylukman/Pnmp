# PNMP Backend — PSSN Network Management Platform

Backend API untuk PNMP menggunakan FastAPI, SQLAlchemy, dan PostgreSQL.

## 📋 Prerequisites

- **Python 3.12+**
- **PostgreSQL 16+**
- **Windows 11** (development environment)

## 🚀 Quick Start

### 1. Setup Virtual Environment

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure Environment

```powershell
copy .env.example .env
```

Edit `.env` dan update:
- `DATABASE_URL` — PostgreSQL connection string
- `APP_SECRET_KEY` — Random secret key (min 32 chars)
- `JWT_SECRET_KEY` — Random secret key for JWT

### 4. Setup PostgreSQL Database

Buka pgAdmin atau psql:

```sql
CREATE DATABASE pnmp;
CREATE USER pnmp WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE pnmp TO pnmp;
```

### 5. Run Database Migration

```powershell
# Initialize alembic (first time only)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

**ATAU** untuk development (auto-create tables):

```powershell
# Tables akan otomatis dibuat saat pertama kali run
```

### 6. Seed Database (Demo Data)

```powershell
python seed.py
```

Ini akan membuat:
- Admin user: `admin` / `admin123`
- Demo users: `neteng1`, `operator1`, `viewer1` (password: `password123`)
- Demo sites dan devices

### 7. Run Backend Server

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Atau:

```powershell
python -m app.main
```

### 8. Access API

- **API**: http://127.0.0.1:8000
- **Swagger Docs**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry
│   ├── core/
│   │   ├── config.py           # Settings (pydantic-settings)
│   │   ├── database.py         # SQLAlchemy engine & session
│   │   ├── security.py         # JWT & password hashing
│   │   └── deps.py             # Dependencies (auth)
│   ├── api/
│   │   ├── router.py           # API router aggregator
│   │   └── v1/
│   │       ├── auth.py         # Authentication endpoints
│   │       ├── users.py        # User management
│   │       ├── sites.py        # Site CRUD
│   │       └── devices.py      # Device CRUD + connection test
│   ├── models/
│   │   └── models.py           # SQLAlchemy ORM models
│   └── schemas/
│       └── schemas.py          # Pydantic request/response schemas
├── alembic/
│   ├── env.py                  # Alembic configuration
│   ├── script.py.mako          # Migration template
│   └── versions/               # Migration files
├── alembic.ini                 # Alembic config
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── seed.py                     # Database seeder
└── README.md                   # This file
```

## 🔌 API Endpoints

### Authentication
- `POST /api/v1/auth/login` — Login (form data)
- `POST /api/v1/auth/login/json` — Login (JSON)

### Users
- `GET /api/v1/users/` — List users
- `GET /api/v1/users/me` — Current user info
- `POST /api/v1/users/` — Create user
- `GET /api/v1/users/{id}` — Get user
- `PUT /api/v1/users/{id}` — Update user
- `DELETE /api/v1/users/{id}` — Delete user

### Sites
- `GET /api/v1/sites/` — List sites
- `POST /api/v1/sites/` — Create site
- `GET /api/v1/sites/{id}` — Get site
- `PUT /api/v1/sites/{id}` — Update site
- `DELETE /api/v1/sites/{id}` — Delete site

### Devices
- `GET /api/v1/devices/` — List devices (with filters)
- `POST /api/v1/devices/` — Create device
- `GET /api/v1/devices/{id}` — Get device
- `PUT /api/v1/devices/{id}` — Update device
- `DELETE /api/v1/devices/{id}` — Delete device
- `POST /api/v1/devices/{id}/test-connection` — Test connectivity
- `POST /api/v1/devices/{id}/credentials` — Set credentials
- `GET /api/v1/devices/{id}/credentials` — Get credentials

## 🔐 Authentication

Semua endpoint (kecuali `/auth/login`) memerlukan JWT token.

### Cara Login:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Gunakan Token:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  http://127.0.0.1:8000/api/v1/devices/
```

## 🗄️ Database Models

### User
- id, username, email, full_name, hashed_password, role, is_active

### Site
- id, name, description, address

### Device
- id, hostname, display_name, management_ip, vendor, model, serial_number
- device_type, device_role, site_id, location, status
- monitoring_enabled, firmware_version, mac_address
- cpu_usage, memory_usage, temperature, uptime, last_seen

### DeviceCredential
- id, device_id, username, encrypted_password
- snmp_version, snmp_community_encrypted, ssh_enabled, api_enabled

### Alert
- id, device_id, severity, title, description, source, status

### EventLog
- id, device_id, category, severity, message, source, timestamp

### TopologyLink
- id, source_device_id, source_interface, target_device_id, target_interface
- link_type, bandwidth, status

## 🛠️ Development

### Run with auto-reload:
```powershell
uvicorn app.main:app --reload
```

### Run tests:
```powershell
pytest
```

### Generate migration:
```powershell
alembic revision --autogenerate -m "description"
```

### Apply migration:
```powershell
alembic upgrade head
```

### Rollback migration:
```powershell
alembic downgrade -1
```

## 🔒 Security Notes

- Password di-hash menggunakan bcrypt
- JWT token dengan expiry time configurable
- CORS configured untuk frontend only
- Credentials device di-encrypt di database
- Jangan commit `.env` file
- Secret keys harus random dan minimal 32 karakter

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | PNMP |
| `APP_ENV` | Environment (development/production) | development |
| `APP_SECRET_KEY` | Application secret key | - |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `JWT_SECRET_KEY` | JWT signing key | - |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | 30 |
| `CORS_ORIGINS` | Allowed origins | localhost:5173 |
| `SNMP_POLL_INTERVAL` | SNMP polling interval (seconds) | 60 |

## 🐛 Troubleshooting

### Database Connection Error
- Pastikan PostgreSQL berjalan
- Cek `DATABASE_URL` di `.env`
- Pastikan database `pnmp` sudah dibuat
- Pastikan user `pnmp` punya akses

### Import Error
- Pastikan virtual environment aktif: `.venv\Scripts\activate`
- Install dependencies: `pip install -r requirements.txt`

### CORS Error
- Cek `CORS_ORIGINS` di `.env`
- Pastikan frontend origin ada di list

## 📄 License

Internal use — PSSN Unit Teknologi Informasi

---

**PNMP V1 — Foundation Phase**
Built with FastAPI + SQLAlchemy + PostgreSQL
