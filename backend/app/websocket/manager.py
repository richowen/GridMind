"""WebSocket connection manager. Broadcasts state updates to all connected browsers.
Sends current state immediately on connect. Handles client disconnects gracefully.

The receive loop uses asyncio.wait_for with a 60-second timeout so that ungracefully
disconnected clients (network drop without TCP FIN) are detected within one minute
rather than hanging indefinitely until OS-level keepalive fires."""

import asyncio
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
        """Full WebSocket lifecycle: connect, send initial state, receive messages, disconnect."""
        await self.connect(websocket)

        # Send complete current state immediately on connect so the browser
        # doesn't show null values until the next 5-minute optimization tick.
        try:
            from app.core.settings_cache import get_setting_float
            from app.database import SessionLocal
            from app.models.optimization import OptimizationResult, SystemState

            db = SessionLocal()
            try:
                latest_opt = (
                    db.query(OptimizationResult)
                    .order_by(OptimizationResult.timestamp.desc())
                    .first()
                )
                latest_state = (
                    db.query(SystemState)
                    .order_by(SystemState.timestamp.desc())
                    .first()
                )

                if latest_opt:
                    # Compute price classification from DB thresholds
                    price_classification = None
                    if latest_opt.current_price_pence is not None:
                        neg_thresh = get_setting_float("price_negative_threshold", 0.0)
                        cheap_thresh = get_setting_float("price_cheap_threshold", 10.0)
                        exp_thresh = get_setting_float("price_expensive_threshold", 25.0)
                        p = latest_opt.current_price_pence
                        if p < neg_thresh:
                            price_classification = "negative"
                        elif p < cheap_thresh:
                            price_classification = "cheap"
                        elif p > exp_thresh:
                            price_classification = "expensive"
                        else:
                            price_classification = "normal"

                    await websocket.send_json({
                        "type": "state",
                        "data": {
                            "battery_soc": latest_opt.current_soc,
                            "battery_mode": latest_state.battery_mode if latest_state else None,
                            "solar_power_kw": latest_opt.current_solar_kw,
                            "solar_forecast_today_kwh": latest_state.solar_forecast_today_kwh if latest_state else None,
                            "solar_forecast_next_hour_kw": latest_state.solar_forecast_next_hour_kw if latest_state else None,
                            "current_price_pence": latest_opt.current_price_pence,
                            "price_classification": price_classification,
                            "recommended_mode": latest_opt.recommended_mode,
                            "decision_reason": latest_opt.decision_reason,
                            "live_charge_rate_kw": None,  # Not stored in DB; populated by next broadcast
                            "last_updated": latest_opt.timestamp.isoformat() if latest_opt.timestamp else None,
                        },
                    })
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Failed to send initial state: {e}")

        try:
            while True:
                # Use a 60-second timeout so ungracefully disconnected clients
                # (network drop without TCP FIN) are detected within one minute
                # rather than hanging indefinitely.
                try:
                    await asyncio.wait_for(websocket.receive_text(), timeout=60)
                except asyncio.TimeoutError:
                    # No message received — send a ping to probe the connection.
                    try:
                        await websocket.send_json({"type": "ping", "data": None})
                    except Exception:
                        # Client is gone — clean up and exit the loop.
                        self.disconnect(websocket)
                        return
        except WebSocketDisconnect:
            self.disconnect(websocket)
        except Exception as e:
            logger.warning(f"WebSocket error: {e}")
            self.disconnect(websocket)


manager = WebSocketManager()
