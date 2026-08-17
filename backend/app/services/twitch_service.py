import urllib.parse
import httpx
import logging
from typing import Optional, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)

TWITCH_AUTH_URL = "https://id.twitch.tv/oauth2/authorize"
TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_HELIX_USERS_URL = "https://api.twitch.tv/helix/users"
TWITCH_HELIX_REDEMPTIONS_URL = "https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions"


def get_oauth_url(telegram_id: int) -> Optional[str]:
    """
    Generates Twitch OAuth 2.0 authorization redirect URL.
    Returns None if TWITCH_CLIENT_ID is not configured.
    """
    client_id = settings.TWITCH_CLIENT_ID.strip()
    if not client_id:
        return None

    redirect_uri = settings.TWITCH_REDIRECT_URI.strip()
    if not redirect_uri:
        base_url = settings.WEBAPP_URL.rstrip("/")
        redirect_uri = f"{base_url}/api/twitch/callback"

    scopes = [
        "user:read:email"
    ]
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "state": str(telegram_id),
        "force_verify": "false"
    }
    
    return f"{TWITCH_AUTH_URL}?{urllib.parse.urlencode(params)}"


async def exchange_code_for_token(code: str) -> Optional[Dict[str, Any]]:
    """
    Exchanges authorization code for Twitch access token.
    """
    if not settings.TWITCH_CLIENT_ID or not settings.TWITCH_CLIENT_SECRET:
        logger.warning("Twitch Client ID / Secret not set in settings.")
        return None

    redirect_uri = settings.TWITCH_REDIRECT_URI
    if not redirect_uri:
        base_url = settings.WEBAPP_URL.rstrip("/")
        redirect_uri = f"{base_url}/api/twitch/callback"

    payload = {
        "client_id": settings.TWITCH_CLIENT_ID,
        "client_secret": settings.TWITCH_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(TWITCH_TOKEN_URL, data=payload)
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.error(f"Twitch token exchange error: {resp.status_code} {resp.text}")
                return None
    except Exception as e:
        logger.error(f"Failed to exchange Twitch code: {e}")
        return None


async def get_twitch_user_info(access_token: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves authenticated Twitch user profile via Helix API.
    """
    client_id = settings.TWITCH_CLIENT_ID or "gp762nuuoqcoxypju8c569th9wz7q5"
    headers = {
        "Client-Id": client_id,
        "Authorization": f"Bearer {access_token}"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(TWITCH_HELIX_USERS_URL, headers=headers)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data:
                    return data[0]
            else:
                logger.error(f"Helix users error: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.error(f"Failed to fetch Twitch user profile: {e}")

    return None
