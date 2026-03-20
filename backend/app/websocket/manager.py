"""WebSocket connection manager. Broadcasts state updates to all connected browsers.
Sends current state immediately on connect. Handles client disconnects gracefully.

The receive loop uses asyncio.wait_for with a 60-second timeout so that ungracefully
disconnected clients (network drop without TCP FIN) are detected within one minute
rather than hanging indefinitely until OS-level keepalive fires."""

import asyncio
import logging
from typing import List, Optional

from fastapi import WebSocket, WebSocketDisconnect

from app.utils import utcnow

logger = logging.getLogger(__name__)


async def _fetch_initial_state(db) -> Optional[dict]:
    """Query DB for the latest optimization result and system state.

    Returns a dict ready to send as the 'state' WebSocket message payload,
    or None if no optimization result exists yet (first boot).

    Extracted from WebSocketManager.handle() so the connection manager stays
    focused on connection lifecycle rather than business logic.
    """
    from app.core.settings_cache import get_settings
    from app.models.optimization import OptimizationResult, SystemState
    from app.models.prices import ElectricityPrice
    from app.services.octopus_energy import get_current_price_classification

    latest_opt = (
        db.query(OptimizationResult)
        .order_by(OptimizationResult.timestamp.desc())
        .first()
    )
    if not latest_opt:
        return None

    latest_state = (
        db.query(SystemState)
        .order_by(SystemState.timestamp.desc())
        .first()
    )

    now = utcnow()
    price_rows = (
        db.query(ElectricityPrice)
        .filter(ElectricityPrice.valid_to >= now)
        .order_by(ElectricityPrice.valid_from)
        .limit(96)
        .all()
    )
    price_classification = get_current_price_classification(price_rows, now, get_settings())

    return {
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
    }


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
            from app.database import SessionLocal
            db = SessionLocal()
            try:
                state = await _fetch_initial_state(db)
                if state:
                    await websocket.send_json({"type": "state", "data": state})
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
