"""ClearWay AI — WebSocket Manager"""
import json
import logging
from datetime import datetime
from typing import Set, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WS client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        if not self.active_connections:
            return
        data = json.dumps(message, default=str)
        dead = set()
        for ws in self.active_connections.copy():
            try:
                await ws.send_text(data)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.active_connections.discard(ws)

    async def broadcast_traffic_update(self, intersections: list):
        await self.broadcast({
            "type": "traffic_update",
            "timestamp": datetime.utcnow().isoformat(),
            "intersections": [i.model_dump() for i in intersections],
        })

    async def broadcast_siren_alert(self, event, dispatch=None):
        await self.broadcast({
            "type": "siren_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "event": event.model_dump() if event else None,
            "dispatch": dispatch.model_dump() if dispatch else None,
        })

    async def broadcast_emergency_update(self, status: dict):
        await self.broadcast({"type": "emergency_update", "timestamp": datetime.utcnow().isoformat(), "status": status})

    async def broadcast_optimization_result(self, result):
        await self.broadcast({"type": "optimization_complete", "timestamp": datetime.utcnow().isoformat(),
                               "result": result.model_dump() if hasattr(result, "model_dump") else result})

    async def broadcast_alert(self, alert):
        await self.broadcast({"type": "new_alert", "timestamp": datetime.utcnow().isoformat(),
                               "alert": alert.model_dump() if hasattr(alert, "model_dump") else alert})

    async def broadcast_system_status(self, status: dict):
        await self.broadcast({"type": "system_status", "timestamp": datetime.utcnow().isoformat(), "status": status})


ws_manager = ConnectionManager()
