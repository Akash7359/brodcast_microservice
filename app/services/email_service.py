from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from pathlib import Path
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "emails"

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_HOST,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_USE_TLS,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=str(TEMPLATE_DIR),
)

fast_mail = FastMail(conf)
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


async def send_email(
    to_email: str,
    subject: str,
    template_path: str,
    template_data: dict,
    cc: str | None = None,
    bcc: str | None = None,
) -> dict:
    """Send templated HTML email."""
    try:
        # Render Jinja2 template
        template_file = template_path.replace(".", "/") + ".html"
        template = jinja_env.get_template(template_file)
        html_body = template.render(**template_data)

        recipients = [to_email]
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            cc=[cc] if cc else [],
            bcc=[bcc] if bcc else [],
            body=html_body,
            subtype=MessageType.html,
        )

        await fast_mail.send_message(message)
        logger.info(f"Email sent to {to_email} via template {template_path}")
        return {"status": "sent", "recipient": to_email}

    except TemplateNotFound as e:
        logger.error(f"Email template not found: {e}")
        return {"status": "failed", "error": f"Template not found: {template_path}"}
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return {"status": "failed", "error": str(e)}
