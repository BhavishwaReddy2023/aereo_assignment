import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Job(Base):
    """Represents a bulk certificate generation job."""
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_name = Column(String(255), nullable=False)
    event_date = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="pending", index=True)
    total_count = Column(Integer, nullable=False, default=0)
    successful_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship to certificates
    certificates = relationship("Certificate", back_populates="job", cascade="all, delete-orphan")


class Certificate(Base):
    """Represents an individual recipient certificate within a job."""
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="pending", index=True)
    file_path = Column(String(512), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Relationship to job
    job = relationship("Job", back_populates="certificates")
