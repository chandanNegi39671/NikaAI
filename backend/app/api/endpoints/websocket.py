"""
backend/app/api/endpoints/websocket.py
"""WebSocket endpoint for real-time live inspections, notifications, and alerts."""

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
        logger.info(
            "WebSocket connected. Total active connections: %s",
            len(self.active_connections),
        )

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        for machine_id, websockets in list(self.active_subscriptions.items()):
            if websocket in websockets:
                websockets.remove(websocket)
                if not websockets:
                    del self.active_subscriptions[machine_id]

        logger.info(
            "WebSocket disconnected. Total active connections: %s",
            len(self.active_connections),
        )

    async def subscribe(self, websocket: WebSocket, machine_id: str) -> None:
        if machine_id not in self.active_subscriptions:
            self.active_subscriptions[machine_id] = []
        if websocket not in self.active_subscriptions[machine_id]:
            self.active_subscriptions[machine_id].append(websocket)

        logger.info("WebSocket subscribed to machine '%s'", machine_id)
        await websocket.send_json(
            {"event": "subscription_success", "machine_id": machine_id}
        )

    async def broadcast_to_machine(self, machine_id: str, data: dict) -> None:
        websockets = self.active_subscriptions.get(machine_id, [])
        dead_sockets = []
        for ws in websockets:
            try:
                await ws.send_json(data)
            except Exception as exc:
                logger.warning("Failed to send to socket: %s", exc)
                dead_sockets.append(ws)

        for dead in dead_sockets:
            self.disconnect(dead)

    async def broadcast_global(self, data: dict) -> None:
        dead_sockets = []
        for ws in self.active_connections:
            try:
                await ws.send_json(data)
            except Exception as exc:
                logger.warning("Failed to send global broadcast: %s", exc)
                dead_sockets.append(ws)

        for dead in dead_sockets:
            self.disconnect(dead)


manager = ConnectionManager()


def _extract_token(websocket: WebSocket) -> str | None:
    auth_header = websocket.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        return token or None
    token = websocket.query_params.get("token")
    return token or None


async def _authenticate_websocket(websocket: WebSocket):
    token = _extract_token(websocket)
    if not token:
        await websocket.close(code=4401)
        return None

    db = SessionLocal()
    try:
        user = await get_current_user(token=token, db=db)
        return user
    except Exception as exc:
        logger.warning("WebSocket authentication failed: %s", exc)
        await websocket.close(code=4401)
        return None
    finally:
        db.close()


@router.websocket("/inspections")
async def websocket_endpoint(websocket: WebSocket):
    user = await _authenticate_websocket(websocket)
    if not user:
        return

    await manager.connect(websocket)
    try:
        while True:
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
                else:
                    await websocket.send_json(
                        {"event": "error", "message": "Unsupported action"}
                    )
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"event": "error", "message": "Invalid JSON format"}
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
        manager.disconnect(websocket)
