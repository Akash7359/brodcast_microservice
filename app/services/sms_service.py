import re
import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

SMS_TEMPLATES: dict[int, str] = {
    1: "Your OTP is {#var#}. Valid for 10 minutes. Do not share.",
    2: "Your password reset OTP is {#var#}.",
    3: "Your payout of Rs.{#var#} has been processed.",
    4: "Welcome! Your account has been created. OTP: {#var#}",
}

INDIAN_MOBILE_RE = re.compile(r"^[6-9]\d{9}$")


def validate_mobile(mobile: str) -> bool:
    return bool(INDIAN_MOBILE_RE.match(mobile))


def resolve_sms_template(category_id: int, var_value: str) -> str | None:
    template = SMS_TEMPLATES.get(category_id)
    if not template:
        return None
    return template.replace("{#var#}", str(var_value))


async def send_sms(mobile: str, category_id: int, var_value: str) -> dict:
    """Send SMS via Gupshup API."""
    if not validate_mobile(mobile):
        return {"status": "failed", "error": "Invalid mobile number format"}

    message = resolve_sms_template(category_id, var_value)
    if not message:
        return {"status": "failed", "error": f"No SMS template for category {category_id}"}

    params = {
        "method": settings.SMS_METHOD,
        "send_to": f"{settings.SMS_SEND_TO_COUNTRY}{mobile}",
        "msg": message,
        "msg_type": "TEXT",
        "userid": settings.SMS_USERID,
        "auth_scheme": "plain",
        "password": settings.SMS_PASSWORD,
        "v": settings.SMS_VERSION,
        "format": "text",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(settings.SMS_API_URL, params=params)
            response.raise_for_status()
            logger.info(f"SMS sent to {mobile}: {response.text}")
            return {"status": "sent", "provider_response": response.text}

    except httpx.HTTPStatusError as e:
        logger.error(f"SMS HTTP error: {e}")
        return {"status": "failed", "error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        logger.error(f"SMS send failed: {e}")
        return {"status": "failed", "error": str(e)}
