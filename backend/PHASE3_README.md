# PNMP Phase 3 — Real Network Monitoring Engine

## 📋 Overview

Phase 3 mengubah PNMP dari Device Inventory menjadi **Real Network Monitoring Platform** dengan kemampuan:

- ✅ SNMP v2c/v3 monitoring
- ✅ Aruba AOS-CX REST API integration
- ✅ Real-time metrics collection
- ✅ Automatic alert generation
- ✅ Event logging
- ✅ WebSocket real-time updates
- ✅ Zabbix integration foundation

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PNMP Backend                          │
├─────────────────────────────────────────────────────────┤
│  FastAPI Application                                     │
│  ├── REST API (v1)                                       │
│  │   ├── /auth, /users, /sites, /devices                │
│  │   ├── /dashboard, /alerts, /events                   │
│  │   ├── /metrics (NEW)                                  │
│  │   └── /integrations/zabbix (NEW)                     │
│  │                                                       │
│  ├── WebSocket (NEW)                                     │
│  │   └── /ws/dashboard                                   │
│  │                                                       │
│  └── Monitoring Engine (NEW)                             │
│      ├── Scheduler (asyncio-based)                       │
│      ├── Manager (orchestration)                         │
│      └── Adapters                                        │
│          ├── GenericSNMPAdapter                          │
│          └── ArubaCXAdapter                              │
└─────────────────────────────────────────────────────────┘
```

---

## 🆕 New Features

### 1. Monitoring Engine

**Location:** `backend/app/monitoring/`

```python
monitoring/
├── __init__.py
├── manager.py          # Orchestration & data storage
├── scheduler.py        # Periodic polling scheduler
└── adapters/
    ├── __init__.py
    ├── base.py         # Abstract adapter interface
    ├── snmp.py         # Generic SNMP adapter
    └── aruba_cx.py     # Aruba AOS-CX REST API
```

**Features:**
- Async polling with concurrency control (semaphore)
- Configurable polling interval (default: 60s)
- Failure threshold before marking device DOWN
- Automatic interface discovery
- Metrics storage with retention
- Alert deduplication

### 2. SNMP Adapter

**Supports:** SNMP v2c and v3

**Collected Data:**
- System info (hostname, uptime, description)
- Interface list (name, status, speed, MTU)
- Interface statistics (64-bit counters)
  - RX/TX bytes
  - RX/TX errors
  - RX/TX discards

**OIDs Used:**
```
sysName: 1.3.6.1.2.1.1.5.0
sysDescr: 1.3.6.1.2.1.1.1.0
sysUpTime: 1.3.6.1.2.1.1.3.0
ifHCInOctets: 1.3.6.1.2.1.31.1.1.1.6
ifHCOutOctets: 1.3.6.1.2.1.31.1.1.1.10
```

### 3. Aruba CX Adapter

**Uses:** Aruba AOS-CX REST API (HTTPS)

**Collected Data:**
- System status (hostname, model, firmware, serial)
- Resource utilization (CPU, memory)
- Interface list and statistics
- VLAN information (future)
- LLDP neighbors (future)

**Authentication:**
- Username/password from encrypted credentials
- Session-based authentication
- Automatic re-authentication on 401

### 4. Metrics API

**Endpoints:**

```
GET /api/v1/devices/{device_id}/metrics
  - Historical CPU, memory, temperature, uptime
  - Query params: from, to, limit

GET /api/v1/interfaces/{interface_id}/metrics
  - Historical traffic, errors, utilization
  - Query params: from, to, limit
```

**Example:**
```bash
curl -H "Authorization: Bearer <token>" \
  "http://127.0.0.1:8000/api/v1/devices/1/metrics?from=2026-01-01T00:00:00&limit=100"
```

### 5. WebSocket Real-time Updates

**Endpoint:** `ws://127.0.0.1:8000/ws/dashboard?token=<jwt>`

**Events:**
```json
{
  "type": "device_status_changed",
  "device_id": 10,
  "status": "DOWN",
  "timestamp": "2026-01-15T10:00:00"
}
```

**Event Types:**
- `device_status_changed`
- `alert_created`
- `alert_resolved`
- `interface_status_changed`

### 6. Zabbix Integration

**Endpoints:**

```
GET  /api/v1/integrations/zabbix/status
POST /api/v1/integrations/zabbix/test
GET  /api/v1/integrations/zabbix/hosts
GET  /api/v1/integrations/zabbix/problems
```

**Configuration:**
```env
ZABBIX_URL=https://zabbix.example.com
ZABBIX_API_TOKEN=your-api-token
```

---

## 📊 Data Flow

### Monitoring Cycle

```
1. Scheduler triggers every 60s
   ↓
2. Get all devices with monitoring_enabled=true
   ↓
3. For each device (concurrent with semaphore):
   a. Get credentials from DB
   b. Decrypt credentials
   c. Select adapter (SNMP/Aruba)
   d. Test connection
   e. If success:
      - Get system info → store DeviceMetric
      - Get interfaces → update DeviceInterface
      - Get interface stats → store InterfaceMetric
      - Update device status to UP
      - Reset failure_count
   f. If failure:
      - Increment failure_count
      - If failure_count >= threshold (3):
        - Set status to DOWN
        - Create alert
        - Create event
   ↓
4. Broadcast WebSocket updates
```

### Alert Generation

```
Device DOWN (failure_count >= 3)
  → Create CRITICAL alert
  → Create DEVICE_DOWN event
  → Broadcast WebSocket

Device UP (recovery)
  → Resolve existing DOWN alerts
  → Create INFO event
  → Broadcast WebSocket

High CPU/Memory/Utilization
  → Create WARNING/HIGH alert
  → Create event
  → Broadcast WebSocket
```

---

## 🔧 Configuration

### Environment Variables

```env
# Monitoring
MONITORING_INTERVAL_SECONDS=60      # Polling interval
MONITOR_FAILURE_THRESHOLD=3         # Failures before DOWN
MONITORING_MAX_CONCURRENCY=10       # Max concurrent polls

# SNMP
SNMP_TIMEOUT=5                      # SNMP timeout (seconds)
SNMP_RETRIES=2                      # SNMP retries

# Aruba CX
ARUBA_API_TIMEOUT=10                # API timeout (seconds)

# Metrics Retention
METRICS_RETENTION_DAYS=30           # Keep metrics for 30 days

# Zabbix (Optional)
ZABBIX_URL=
ZABBIX_API_TOKEN=
```

---

## 🚀 Usage

### 1. Install Dependencies

```powershell
cd backend
.venv\Scripts\activate
pip install -r requirements.txt
```

**New dependencies:**
- `pysnmp-lextudio==6.1.2` — SNMP library
- `paramiko==3.5.0` — SSH library (future)
- `websockets==14.1` — WebSocket support

### 2. Run Database Migration

```powershell
alembic revision --autogenerate -m "phase3_monitoring"
alembic upgrade head
```

### 3. Start Backend

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**You should see:**
```
INFO:     Starting PNMP v1.0.0
INFO:     Database tables created/verified
INFO:     Monitoring scheduler started
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 4. Configure Device Credentials

**Via API:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/devices/1/credentials \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "snmp_version": "v2c",
    "snmp_community": "public",
    "snmp_enabled": true
  }'
```

**For Aruba CX:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/devices/2/credentials \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your-password",
    "api_enabled": true
  }'
```

### 5. Enable Monitoring

```bash
curl -X PUT http://127.0.0.1:8000/api/v1/devices/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "monitoring_enabled": true,
    "monitoring_method": "snmp"
  }'
```

### 6. Test Connection

```bash
curl -X POST http://127.0.0.1:8000/api/v1/devices/1/test-connection \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "success": true,
  "device_id": 1,
  "method": "SNMP",
  "latency_ms": 4.5,
  "message": "SNMP connection successful to 10.0.0.1"
}
```

### 7. View Metrics

```bash
curl -H "Authorization: Bearer <token>" \
  "http://127.0.0.1:8000/api/v1/devices/1/metrics?limit=10"
```

**Response:**
```json
{
  "device_id": 1,
  "metrics": [
    {
      "timestamp": "2026-01-15T10:00:00",
      "cpu_percent": 25,
      "memory_percent": 45,
      "temperature": 42,
      "uptime_seconds": 86400
    }
  ]
}
```

### 8. Connect WebSocket

**JavaScript:**
```javascript
const token = localStorage.getItem('pnmp_token');
const ws = new WebSocket(`ws://127.0.0.1:8000/ws/dashboard?token=${token}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('WebSocket event:', data);
  
  if (data.type === 'device_status_changed') {
    // Update UI
  }
};
```

---

## 📝 New API Endpoints

### Metrics

```
GET /api/v1/devices/{device_id}/metrics
GET /api/v1/interfaces/{interface_id}/metrics
```

### Integrations

```
GET  /api/v1/integrations/zabbix/status
POST /api/v1/integrations/zabbix/test
GET  /api/v1/integrations/zabbix/hosts
GET  /api/v1/integrations/zabbix/problems
```

### WebSocket

```
WS /ws/dashboard?token=<jwt>
```

---

## 🔒 Security

### Credential Handling

- All credentials encrypted at rest (Fernet/AES)
- Decrypted only in memory during monitoring
- Never exposed via API responses
- GET /credentials returns only status flags

### WebSocket Authentication

- JWT token required in query parameter
- Invalid tokens rejected with 1008 code
- Connections verified on each message

---

## 🧪 Testing

### Test SNMP Monitoring

```powershell
# 1. Configure SNMP credentials
curl -X POST http://127.0.0.1:8000/api/v1/devices/1/credentials \
  -H "Authorization: Bearer <token>" \
  -d '{"snmp_version": "v2c", "snmp_community": "public"}'

# 2. Enable monitoring
curl -X PUT http://127.0.0.1:8000/api/v1/devices/1 \
  -H "Authorization: Bearer <token>" \
  -d '{"monitoring_enabled": true, "monitoring_method": "snmp"}'

# 3. Test connection
curl -X POST http://127.0.0.1:8000/api/v1/devices/1/test-connection \
  -H "Authorization: Bearer <token>"

# 4. Wait 60s for scheduler to poll

# 5. Check metrics
curl -H "Authorization: Bearer <token>" \
  "http://127.0.0.1:8000/api/v1/devices/1/metrics"
```

### Test Aruba CX Monitoring

```powershell
# 1. Configure API credentials
curl -X POST http://127.0.0.1:8000/api/v1/devices/2/credentials \
  -H "Authorization: Bearer <token>" \
  -d '{"username": "admin", "password": "password", "api_enabled": true}'

# 2. Set monitoring method to REST_API
curl -X PUT http://127.0.0.1:8000/api/v1/devices/2 \
  -H "Authorization: Bearer <token>" \
  -d '{"monitoring_enabled": true, "monitoring_method": "rest_api", "vendor": "Aruba"}'

# 3. Test connection
curl -X POST http://127.0.0.1:8000/api/v1/devices/2/test-connection \
  -H "Authorization: Bearer <token>"
```

---

## 📊 Database Changes

### New Tables

- `device_metrics` — Historical device performance
- `interface_metrics` — Historical interface traffic

### Updated Tables

- `devices` — Added `monitoring_method`, `failure_count`
- `device_interfaces` — Added `if_index`, `admin_status`, `speed_bps`, traffic counters
- `alerts` — Added `interface_id`, `acknowledged_by`, `resolved_by`
- `event_logs` — Added `event_type`, `interface_id`

---

## 🎯 Next Steps (Phase 4)

- [ ] Traffic rate calculation (delta bytes / delta time)
- [ ] Interface utilization calculation
- [ ] Metrics aggregation (hourly, daily)
- [ ] Metrics cleanup job (retention policy)
- [ ] SSH adapter for legacy devices
- [ ] Syslog receiver
- [ ] SNMP trap receiver
- [ ] Topology auto-discovery (LLDP/CDP)
- [ ] Configuration backup
- [ ] Email/Telegram notifications

---

## 📚 Documentation

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc
- **Health Check:** http://127.0.0.1:8000/health

---

## 🐛 Troubleshooting

### SNMP Connection Failed

1. Check SNMP service is running on device
2. Verify community string/credentials
3. Check firewall allows UDP 161
4. Test with snmpwalk: `snmpwalk -v2c -c public <ip>`

### Aruba CX Connection Failed

1. Verify REST API is enabled on device
2. Check username/password
3. Verify HTTPS certificate (self-signed OK)
4. Check firewall allows TCP 443

### Monitoring Not Running

1. Check logs for scheduler errors
2. Verify `MONITORING_INTERVAL_SECONDS` is set
3. Check device has `monitoring_enabled=true`
4. Verify credentials are configured

### Metrics Not Showing

1. Wait for at least one polling cycle (60s default)
2. Check device status is UP
3. Verify monitoring scheduler is running (`/health`)
4. Check database for metrics records

---

## ✅ Phase 3 Checklist

- [x] Monitoring engine architecture
- [x] SNMP v2c/v3 adapter
- [x] Aruba CX REST API adapter
- [x] Monitoring scheduler (asyncio)
- [x] Metrics API endpoints
- [x] WebSocket real-time updates
- [x] Alert generation & deduplication
- [x] Event logging
- [x] Zabbix integration foundation
- [x] Credential encryption
- [x] Failure threshold handling
- [x] Interface auto-discovery
- [x] Health check with monitoring status

---

**PNMP Phase 3 — Real Network Monitoring Engine** ✅
