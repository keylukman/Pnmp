# PNMP — PSSN Network Management Platform

Platform Network Management System (NMS) untuk Unit Teknologi Informasi PSSN.

## 📋 Overview

PNMP adalah aplikasi enterprise untuk mengelola, memonitor, dan menginventarisasi perangkat jaringan dalam lingkungan kampus.

**Tech Stack:**
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS + ECharts
- **Backend:** Python 3.12+ + FastAPI + SQLAlchemy + PostgreSQL
- **Database:** PostgreSQL 16+

## 🏗️ Project Structure

```
PNMP/
├── frontend/           → React SPA (yang ini)
│   ├── src/
│   │   ├── pages/      → Halaman aplikasi
│   │   ├── stores/     → Zustand stores
│   │   ├── services/   → API service
│   │   └── layouts/    → Layout components
│   └── package.json
│
├── backend/            → FastAPI REST API
│   ├── app/
│   │   ├── api/        → API routes
│   │   ├── core/       → Config, DB, Security
│   │   ├── models/     → SQLAlchemy models
│   │   └── schemas/    → Pydantic schemas
│   ├── requirements.txt
│   └── README.md
│
└── README.md           → File ini
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** LTS (18+)
- **Python** 3.12+
- **PostgreSQL** 16+
- **Git**

---

### 1. Frontend Setup

```powershell
# Di folder frontend (atau root project ini)
npm install
npm run dev
```

Frontend akan berjalan di: **http://localhost:5173**

---

### 2. Backend Setup

```powershell
cd backend

# Buat virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env
```

Edit `backend/.env`:
```env
DATABASE_URL=postgresql+psycopg://pnmp:password@localhost:5432/pnmp
APP_SECRET_KEY=your-random-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

### 3. Database Setup

Buka pgAdmin atau psql:

```sql
CREATE DATABASE pnmp;
CREATE USER pnmp WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE pnmp TO pnmp;
```

### 4. Seed Database

```powershell
cd backend
.venv\Scripts\activate
python seed.py
```

Ini akan membuat:
- **Admin:** `admin` / `admin123`
- **Demo users:** `neteng1` / `password123`

### 5. Run Backend

```powershell
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend akan berjalan di: **http://127.0.0.1:8000**
Swagger docs: **http://127.0.0.1:8000/docs**

---

## 🔐 Login

| Mode | Username | Password |
|------|----------|----------|
| Backend aktif | `admin` | `admin123` |
| Demo (tanpa backend) | apapun | apapun |

Frontend akan otomatis detect apakah backend tersedia. Jika tidak, akan menggunakan demo mode dengan data lokal.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login/json` | Login |
| GET | `/api/v1/users/me` | Current user |
| GET | `/api/v1/sites/` | List sites |
| POST | `/api/v1/sites/` | Create site |
| GET | `/api/v1/devices/` | List devices |
| POST | `/api/v1/devices/` | Create device |
| PUT | `/api/v1/devices/{id}` | Update device |
| DELETE | `/api/v1/devices/{id}` | Delete device |
| POST | `/api/v1/devices/{id}/test-connection` | Test ping |

Full docs: **http://127.0.0.1:8000/docs**

---

## 📦 Features (V1)

### ✅ Completed

- [x] Login & Authentication (JWT)
- [x] NOC Dashboard
- [x] Device Inventory (CRUD)
- [x] Device Detail Page
- [x] Site Management
- [x] Interface Monitoring
- [x] Alert Management
- [x] Network Topology
- [x] WAN Monitoring + SLA
- [x] Reports
- [x] User Management (RBAC)
- [x] Settings
- [x] Backend API (Foundation)
- [x] Database Models
- [x] Authentication API
- [x] Device CRUD API
- [x] Site CRUD API

### 🔄 Next Phase

- [ ] SNMP Polling Worker
- [ ] Aruba AOS-CX API Adapter
- [ ] SSH Connector
- [ ] Zabbix Integration
- [ ] WebSocket Real-time Updates
- [ ] Email Notifications
- [ ] PDF Report Export

---

## 🛠️ Development

### Frontend

```powershell
npm run dev       # Development server
npm run build     # Production build
npm run preview   # Preview production build
```

### Backend

```powershell
cd backend
.venv\Scripts\activate

uvicorn app.main:app --reload     # Dev server
python seed.py                     # Seed database
alembic upgrade head              # Run migrations
alembic revision --autogenerate -m "desc"  # Create migration
```

---

## 📝 Environment Variables

### Backend (.env)

```env
APP_NAME=PNMP
APP_ENV=development
APP_SECRET_KEY=change-me-32-chars-min
DATABASE_URL=postgresql+psycopg://pnmp:password@localhost:5432/pnmp
JWT_SECRET_KEY=change-me-jwt-secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=["http://localhost:5173"]
SNMP_POLL_INTERVAL=60
```

---

## 🐛 Troubleshooting

### Frontend tidak connect ke backend?
- Pastikan backend running di port 8000
- Cek CORS_ORIGINS di .env backend
- Buka browser console untuk lihat error

### Database connection error?
- Pastikan PostgreSQL running
- Cek DATABASE_URL di .env
- Pastikan database `pnmp` sudah dibuat

### Import error di backend?
- Pastikan virtual environment aktif
- `pip install -r requirements.txt`

---

## 📄 License

Internal — PSSN Unit Teknologi Informasi

---

**PNMP V1.0** — Foundation Phase ✅
