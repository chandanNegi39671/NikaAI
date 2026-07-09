"""
backend/app/api/endpoints/websocket.py
───────────────────────────────────────
WebSocket endpoint for real-time live inspections, notifications, and alerts.
"""

import json
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/ws",
    tags=["Real-time WebSockets"],
)


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts events."""

    def __init__(self):
        # Maps machine_id -> list of WebSockets subscribed
        self.active_subscriptions: Dict[str, List[WebSocket]] = {}
        # List of all open WebSockets
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"WebSocket connected. Total active connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        # Clean up subscriptions
        for machine_id, websockets in list(self.active_subscriptions.items()):
            if websocket in websockets:
                websockets.remove(websocket)
                if not websockets:
                    del self.active_subscriptions[machine_id]
        logger.info(
            f"WebSocket disconnected. Total active connections: {len(self.active_connections)}"
        )

    async def subscribe(self, websocket: WebSocket, machine_id: str):
        """Subscribe a connection to events from a specific factory machine."""
        if machine_id not in self.active_subscriptions:
            self.active_subscriptions[machine_id] = []
        if websocket not in self.active_subscriptions[machine_id]:
            self.active_subscriptions[machine_id].append(websocket)
        logger.info(f"WebSocket subscribed to machine '{machine_id}'")
        await websocket.send_json(
            {"event": "subscription_success", "machine_id": machine_id}
        )

    async def broadcast_to_machine(self, machine_id: str, data: dict):
        """Send message only to connections subscribed to a specific machine."""
        websockets = self.active_subscriptions.get(machine_id, [])
        dead_sockets = []
        for ws in websockets:
            try:
                await ws.send_json(data)
            except Exception as exc:
                logger.warning(f"Failed to send to socket: {exc}")
                dead_sockets.append(ws)

        for dead in dead_sockets:
            self.disconnect(dead)

    async def broadcast_global(self, data: dict):
        """Send message to all open WebSocket connections."""
        dead_sockets = []
        for ws in self.active_connections:
            try:
                await ws.send_json(data)
            except Exception as exc:
                logger.warning(f"Failed to send global broadcast: {exc}")
                dead_sockets.append(ws)

        for dead in dead_sockets:
            self.disconnect(dead)


manager = ConnectionManager()


@router.websocket("/inspections")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Handle incoming client requests (e.g. subscribe to machine)
            data_str = await websocket.receive_text()
            try:
                data = json.loads(data_str)
                action = data.get("action")

                if action == "subscribe":
                    machine_id = data.get("machine_id")
                    if machine_id:
                        await manager.subscribe(websocket, machine_id)
                elif action == "ping":
                    await websocket.send_json({"event": "pong"})
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"event": "error", "message": "Invalid JSON format"}
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.error(f"WebSocket error: {exc}")
        manager.disconnect(websocket)
