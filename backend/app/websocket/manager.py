"""WebSocket connection manager. Broadcasts state updates to all connected browsers.
Sends current state immediately on connect. Handles client disconnects gracefully."""

import logging
from typing import List

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.debug(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.debug(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict) -> None:
        """Send a JSON message to all connected browsers. Removes dead connections."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    async def handle(self, websocket: WebSocket) -> None:
        """Full WebSocket lifecycle: connect, receive messages, disconnect."""
        await self.connect(websocket)

        # Send current state immediately on connect
        try:
            from app.database import SessionLocal
            from app.models.optimization import OptimizationResult
            db = SessionLocal()
            try:
                latest = (
                    db.query(OptimizationResult)
                    .order_by(OptimizationResult.timestamp.desc())
                    .first()
                )
                if latest:
                    await websocket.send_json({
                        "type": "state",
                        "data": {
                            "battery_soc": latest.current_soc,
                            "current_price_pence": latest.current_price_pence,
                            "solar_power_kw": latest.current_solar_kw,
                            "recommended_mode": latest.recommended_mode,
                            "decision_reason": latest.decision_reason,
                            "last_updated": latest.timestamp.isoformat() if latest.timestamp else None,
                        },
                    })
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Failed to send initial state: {e}")

        try:
            while True:
                data = await websocket.receive_text()
                if data == "refresh":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            self.disconnect(websocket)
        except Exception as e:
            logger.warning(f"WebSocket error: {e}")
            self.disconnect(websocket)


manager = WebSocketManager()
