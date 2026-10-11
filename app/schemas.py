from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from app.config import settings

class RecipientInput(BaseModel):
    """Schema for individual recipient input validation."""
    name: str = Field(..., min_length=1, max_length=255, description="Full name of the recipient")
    email: EmailStr = Field(..., description="Valid email address of the recipient")

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Recipient name cannot be empty or only whitespace")
        return stripped


class JobCreateRequest(BaseModel):
    """Schema for POST /jobs payload validation."""
    event_name: str = Field(..., min_length=1, max_length=255, description="Name of the event or course")
    event_date: str = Field(..., min_length=1, max_length=100, description="Completion date string (e.g., YYYY-MM-DD or October 9, 2026)")
    recipients: List[RecipientInput] = Field(..., min_length=1, description="List of recipient details")

    @field_validator("event_name", "event_date")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or only whitespace")
        return stripped

    @field_validator("recipients")
    @classmethod
    def validate_recipient_count(cls, v: List[RecipientInput]) -> List[RecipientInput]:
        if not v:
            raise ValueError("Recipient list cannot be empty")
        if len(v) > settings.MAX_RECIPIENTS_PER_REQUEST:
            raise ValueError(f"Recipient list exceeds maximum allowed limit of {settings.MAX_RECIPIENTS_PER_REQUEST}")
        return v


class CertificateResponse(BaseModel):
    """Schema for certificate information in API responses."""
    id: str
    certificate_id: str
    job_id: str
    recipient_name: str
    recipient_email: str
    status: str
    file_path: Optional[str] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobSummaryResponse(BaseModel):
    """Summary response for job creation and status tracking."""
    id: str
    job_id: str
    event_name: str
    event_date: str
    status: str
    total_count: int
    successful_count: int
    failed_count: int
    pending_count: int
    processing_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class JobDetailResponse(JobSummaryResponse):
    """Detailed response for GET /jobs/{job_id}, including all certificates."""
    certificates: List[CertificateResponse] = []
