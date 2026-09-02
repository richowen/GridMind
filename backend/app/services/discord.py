"""Discord webhook client for system alerts (e.g. heater stall detection).
Posts plain-text messages to a user-configured Discord webhook URL."""

import logging

import httpx

from app.core.settings_cache import get_setting

logger = logging.getLogger(__name__)


async def send_discord_alert(message: str) -> bool:
    """POST message to the configured Discord webhook. Returns True on success,
    False if no webhook is configured or the request fails (never raises)."""
    webhook_url = get_setting("discord_webhook_url", "")
    if not webhook_url.strip():
        logger.warning("Discord alert skipped — discord_webhook_url is not configured")
        return False

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook_url, json={"content": message})
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Discord alert failed to send: {e}")
        return False
