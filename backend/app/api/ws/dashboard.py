"""
WebSocket API
Real-time updates for dashboard
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Set
import asyncio
import json
from datetime import datetime
from ...core.database import SessionLocal
from ...core.security import decode_access_token
from ...models import Device, Alert, DeviceStatus, AlertStatus

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.add(connection)
        
        # Clean up disconnected
        self.active_connections -= disconnected


# Global connection manager
manager = ConnectionManager()


async def verify_ws_token(websocket: WebSocket) -> bool:
    """Verify JWT token from query parameter"""
    token = websocket.query_params.get("token")
    if not token:
        return False
    
    payload = decode_access_token(token)
    return payload is not None


@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.
    
    Events sent:
    - device_status_changed
    - alert_created
    - alert_resolved
    - interface_status_changed
    
    Connection:
    ws://localhost:8000/ws/dashboard?token=<jwt_token>
    """
    # Verify authentication
    if not await verify_ws_token(websocket):
        await websocket.close(code=1008, reason="Unauthorized")
        return
    
    await manager.connect(websocket)
    
    try:
        # Send initial state
        db = SessionLocal()
        try:
            initial_state = await _get_dashboard_state(db)
            await websocket.send_json({
                "type": "initial_state",
                "data": initial_state,
                "timestamp": datetime.utcnow().isoformat()
            })
        finally:
            db.close()
        
        # Keep connection alive
        while True:
            # Receive ping/pong or commands
            data = await websocket.receive_text()
            
            # Handle client commands
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)


async def _get_dashboard_state(db: Session) -> dict:
    """Get current dashboard state"""
    # Device counts
    total = db.query(Device).count()
    up = db.query(Device).filter(Device.status == DeviceStatus.UP).count()
    down = db.query(Device).filter(Device.status == DeviceStatus.DOWN).count()
    warning = db.query(Device).filter(Device.status == DeviceStatus.WARNING).count()
    unknown = db.query(Device).filter(Device.status == DeviceStatus.UNKNOWN).count()
    maintenance = db.query(Device).filter(Device.status == DeviceStatus.MAINTENANCE).count()
    
    # Active alerts
    active_alerts = db.query(Alert).filter(
        Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED])
    ).count()
    
    return {
        "total_devices": total,
        "devices_up": up,
        "devices_down": down,
        "devices_warning": warning,
        "devices_unknown": unknown,
        "devices_maintenance": maintenance,
        "active_alerts": active_alerts
    }


async def broadcast_device_status(device_id: int, status: str):
    """Broadcast device status change"""
    await manager.broadcast({
        "type": "device_status_changed",
        "device_id": device_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_alert_created(alert_id: int, device_id: int, severity: str, title: str):
    """Broadcast new alert"""
    await manager.broadcast({
        "type": "alert_created",
        "alert_id": alert_id,
        "device_id": device_id,
        "severity": severity,
        "title": title,
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_alert_resolved(alert_id: int, device_id: int):
    """Broadcast alert resolution"""
    await manager.broadcast({
        "type": "alert_resolved",
        "alert_id": alert_id,
        "device_id": device_id,
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_interface_status(device_id: int, interface_name: str, status: str):
    """Broadcast interface status change"""
    await manager.broadcast({
        "type": "interface_status_changed",
        "device_id": device_id,
        "interface_name": interface_name,
        "status": status,
        "timestamp": datetime.utcnow().isoformat()
    })
