from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.db.session import get_db
from app.models.models import SMTPDetail, ProductCategoryTemplateMapping, CategoryType
from app.schemas.schemas import (
    SendSMTPRequest, SendSMTPResponse,
    GenerateHashRequest, GenerateHashResponse,
    CategoryTypeResponse, BroadcastChannelType,
)
from app.services.email_service import send_email
from app.services.sms_service import send_sms
from app.core.security import generate_hash, verify_hash, is_hash_expired
from app.utils.response_helper import success_response, error_response

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/send-smtp", response_model=SendSMTPResponse, tags=["Messaging"])
async def send_smtp(
    request: Request,
    body: SendSMTPRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Primary messaging endpoint.
    - Channel 1: Email only
    - Channel 2: SMS only
    - Channel 3: Email + SMS
    Protected by: HMAC hash verification + per-IP rate limiting.
    """
    # --- Hash verification ---
    payload_dict = body.model_dump(exclude={"hash"})
    if is_hash_expired(body.timestamp):
        raise HTTPException(status_code=400, detail="Request hash has expired.")
    if not verify_hash(payload_dict, body.hash):
        raise HTTPException(status_code=400, detail="Invalid request hash.")

    # --- Persist pending log ---
    log = SMTPDetail(
        project_id=body.project_id,
        category_type_id=body.category_type_id,
        broadcast_channel_type=body.broadcast_channel_type,
        recipient_email=body.to_email,
        recipient_mobile=body.mobile,
        request_payload=payload_dict,
        status=1,
        request_ip=request.client.host if request.client else None,
        request_path=str(request.url.path),
    )
    db.add(log)
    await db.flush()  # Get ID without committing

    # --- Template lookup ---
    stmt = select(ProductCategoryTemplateMapping).where(
        ProductCategoryTemplateMapping.project_id == body.project_id,
        ProductCategoryTemplateMapping.category_type_id == body.category_type_id,
    )
    result = await db.execute(stmt)
    mapping = result.scalars().first()

    if not mapping:
        log.status = 3
        log.response_payload = {"error": "No template mapping found"}
        raise HTTPException(
            status_code=404,
            detail=f"No template mapping found for project {body.project_id}, category {body.category_type_id}",
        )

    email_result = None
    sms_result = None

    # --- Email dispatch ---
    if body.broadcast_channel_type in (BroadcastChannelType.EMAIL, BroadcastChannelType.BOTH):
        if not body.to_email:
            raise HTTPException(status_code=422, detail="to_email required for email channel.")
        email_result = await send_email(
            to_email=body.to_email,
            subject=mapping.subject or "Notification",
            template_path=mapping.template_path,
            template_data=body.data or {},
            cc=body.cc_email,
            bcc=body.bcc_email,
        )

    # --- SMS dispatch ---
    if body.broadcast_channel_type in (BroadcastChannelType.SMS, BroadcastChannelType.BOTH):
        if not body.mobile:
            raise HTTPException(status_code=422, detail="mobile required for SMS channel.")
        otp_value = (body.data or {}).get("otp", "")
        sms_result = await send_sms(
            mobile=body.mobile,
            category_id=body.category_type_id,
            var_value=otp_value,
        )

    # --- Determine final status ---
    email_ok = email_result is None or email_result.get("status") == "sent"
    sms_ok = sms_result is None or sms_result.get("status") == "sent"
    final_status = 2 if (email_ok and sms_ok) else 3

    log.status = final_status
    log.response_payload = {
        "email": email_result,
        "sms": sms_result,
    }

    logger.info(f"Request #{log.id}: status={final_status}")

    return SendSMTPResponse(
        success=final_status == 2,
        message="Message dispatched successfully" if final_status == 2 else "Partial or full dispatch failure",
        request_id=log.id,
        email_status=email_result.get("status") if email_result else None,
        sms_status=sms_result.get("status") if sms_result else None,
    )


@router.post("/generate-hash", response_model=GenerateHashResponse, tags=["Utilities"])
async def generate_hash_key(body: GenerateHashRequest):
    """Generate HMAC-SHA256 hash for a given payload. Use for testing/integration."""
    hash_value = generate_hash(body.payload)
    return GenerateHashResponse(hash=hash_value)


@router.get("/get-categories-list", response_model=list[CategoryTypeResponse], tags=["Utilities"])
async def get_categories_list(db: AsyncSession = Depends(get_db)):
    """Return all available category types."""
    result = await db.execute(select(CategoryType))
    categories = result.scalars().all()
    return categories
