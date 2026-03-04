from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Any, Dict
from enum import IntEnum


class BroadcastChannelType(IntEnum):
    EMAIL = 1
    SMS = 2
    BOTH = 3


class SendSMTPRequest(BaseModel):
    project_id: int = Field(..., description="Project identifier")
    category_type_id: int = Field(..., description="Message category identifier")
    broadcast_channel_type: BroadcastChannelType = Field(..., description="1=Email, 2=SMS, 3=Both")
    hash: str = Field(..., description="HMAC-SHA256 authentication hash")
    timestamp: int = Field(..., description="Unix timestamp for hash expiry check")

    # Email fields
    to_email: Optional[EmailStr] = None
    cc_email: Optional[EmailStr] = None
    bcc_email: Optional[EmailStr] = None

    # SMS fields
    mobile: Optional[str] = None

    # Dynamic template variables
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v):
        if v and not __import__("re").match(r"^[6-9]\d{9}$", v):
            raise ValueError("Invalid Indian mobile number format")
        return v

    @field_validator("to_email")
    @classmethod
    def require_email_for_email_channel(cls, v, info):
        channel = info.data.get("broadcast_channel_type")
        if channel in (BroadcastChannelType.EMAIL, BroadcastChannelType.BOTH) and not v:
            raise ValueError("to_email is required for email channel")
        return v


class GenerateHashRequest(BaseModel):
    payload: Dict[str, Any]


class GenerateHashResponse(BaseModel):
    hash: str
    message: str = "Hash generated successfully"


class CategoryTypeResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class SendSMTPResponse(BaseModel):
    success: bool
    message: str
    request_id: Optional[int] = None
    email_status: Optional[str] = None
    sms_status: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: Optional[Any] = None
    version: Optional[str] = None
    timestamp: Optional[str] = None
