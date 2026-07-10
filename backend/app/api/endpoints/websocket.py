"""
backend/app/api/endpoints/websocket.py
WebSocket endpoint for real-time live inspections, notifications, and alerts.
"""
import json
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.auth import get_current_user
from app.core.database import SessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/ws",
    tags=["Real-time WebSockets"],
)

class ConnectionManager:
    """Manages active WebSocket connections and broadcasts events."""

    def __init__(self):
        self.active_subscriptions: Dict[str, List[WebSocket]] = {}
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@router.websocket("/live")
async def websocket_live(websocket: WebSocket):
    """Live inspection WebSocket endpoint."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"status": "received", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.websocket("/notifications")
async def websocket_notifications(websocket: WebSocket):
    """Notification broadcast WebSocket endpoint."""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
