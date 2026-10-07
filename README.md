# PNMP — PSSN Network Management Platform

Platform Network Management System (NMS) untuk mengelola, memonitor, dan menginventarisasi perangkat jaringan dalam lingkungan kampus/enterprise.

## 📋 Prerequisites

Sebelum memulai, pastikan sudah terinstall:

| Software | Versi Minimal | Download |
|----------|---------------|----------|
| **Node.js** | LTS (v18+) | https://nodejs.org |
| **Git** | v2.30+ | https://git-scm.com |
| **VS Code** | Latest | https://code.visualstudio.com |

### Untuk Full Stack (Phase selanjutnya):
| Software | Versi Minimal | Download |
|----------|---------------|----------|
| **Python** | 3.12+ | https://python.org |
| **PostgreSQL** | 16+ | https://postgresql.org |

---

## 🚀 Quick Start (Frontend Only)

### 1. Install Dependencies

Buka **PowerShell** atau **Terminal**, lalu:

```powershell
# Masuk ke folder project
cd PNMP

# Install semua dependency frontend
npm install
```

### 2. Jalankan Development Server

```powershell
npm run dev
```

Aplikasi akan berjalan di:
```
http://localhost:3000
```

### 3. Login

```
Username: admin
Password: admin
```

### 4. Build untuk Production

```powershell
npm run build
```

Hasil build ada di folder `dist/`.

---

## 📁 Struktur Project

```
PNMP/
├── src/
│   ├── App.tsx              # Router utama
│   ├── main.tsx             # Entry point
│   ├── index.css            # Global styles + NOC theme
│   ├── layouts/
│   │   └── MainLayout.tsx   # Layout sidebar + header
│   ├── pages/
│   │   ├── LoginPage.tsx    # Halaman login
│   │   ├── DashboardPage.tsx    # NOC Dashboard
│   │   ├── DevicesPage.tsx      # Device inventory
│   │   ├── InterfacesPage.tsx   # Interface monitoring
│   │   ├── AlertsPage.tsx       # Alert management
│   │   ├── TopologyPage.tsx     # Network topology
│   │   ├── WanPage.tsx          # WAN/ISP monitoring
│   │   ├── SitesPage.tsx        # Site management
│   │   ├── ReportsPage.tsx      # Reports
│   │   ├── UsersPage.tsx        # User management
│   │   └── SettingsPage.tsx     # Platform settings
│   └── stores/
│       ├── auth.ts          # Auth state (Zustand)
│       └── devices.ts       # Device data store
├── index.html
├── package.json
├── vite.config.js
├── tsconfig.json
└── README.md
```

---

## 🎨 Fitur yang Tersedia (Frontend V1)

### ✅ Sudah Diimplementasi:
- [x] Login / Authentication
- [x] NOC Dashboard dengan grafik real-time
- [x] Device Inventory (CRUD)
- [x] Interface Monitoring
- [x] Alert Management
- [x] Network Topology
- [x] WAN Monitoring + SLA
- [x] Site Management
- [x] Reports
- [x] User Management (RBAC)
- [x] Settings (SNMP, Monitoring, Security)
- [x] Dark NOC Theme
- [x] Responsive Layout

### 🔜 Phase Selanjutnya (Backend):
- [ ] FastAPI Backend
- [ ] PostgreSQL Database
- [ ] SNMP Monitoring (pysnmp)
- [ ] Aruba AOS-CX API Adapter
- [ ] SSH Connector (Paramiko)
- [ ] Zabbix Integration
- [ ] WebSocket Real-time Updates
- [ ] Background Monitoring Worker
- [ ] Alembic Migrations

---

## 🛠️ Development

```powershell
# Development server (hot reload)
npm run dev

# Type checking
npm run typecheck

# Build production
npm run build
```

---

## 🔧 Troubleshooting

### Port 3000 sudah dipakai?
```powershell
# Cek proses yang menggunakan port 3000
netstat -ano | findstr :3000

# Kill proses (ganti PID dengan nomor yang ditemukan)
taskkill /PID <PID> /F
```

### npm install error?
```powershell
# Hapus node_modules dan install ulang
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

### Node.js version lama?
```powershell
# Cek versi
node --version

# Update ke LTS dari https://nodejs.org
```

---

## 📊 Tech Stack

### Frontend
- **React 18** — UI Framework
- **TypeScript** — Type safety
- **Vite** — Build tool
- **Tailwind CSS 4** — Styling
- **Zustand** — State management
- **React Router** — Navigation
- **ECharts** — Charts & graphs
- **Lucide React** — Icons

---

## 📝 Lisensi

Internal use — PSSN Network Management Platform

---

**PNMP v1.0.0** — PSSN Network Management Platform
