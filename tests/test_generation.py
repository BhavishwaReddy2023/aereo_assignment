import os
from pathlib import Path
import pytest
from app.models import Job, Certificate
from app.services.certificate_generator import (
    generate_certificate_pdf,
    calculate_name_font_size
)
from app.services.job_processor import process_bulk_job
from tests.conftest import TestingSessionLocal

def test_calculate_name_font_size():
    """Test dynamic font size calculation for different name lengths."""
    assert calculate_name_font_size("Alice Smith") == 36  # 11 chars
    assert calculate_name_font_size("Dr. Alexander Christopher Montgomery") == 22  # 38 chars
    assert calculate_name_font_size("Professor Bartholomew Dominick Harrington-Smythe III") == 18  # 52 chars
    assert calculate_name_font_size("Short Name") == 36  # 10 chars

def test_generate_certificate_pdf_real(tmp_path):
    """Test generating a real PDF file on disk."""
    cert_id = "test-uuid-123"
    recipient = "Jane Doe"
    event = "Backend Architecture Mastery"
    date = "October 9, 2026"

    rel_path = generate_certificate_pdf(
        certificate_id=cert_id,
        recipient_name=recipient,
        event_name=event,
        completion_date=date,
        output_dir=tmp_path
    )

    pdf_file = tmp_path / f"{cert_id}.pdf"
    assert pdf_file.exists()
    assert pdf_file.stat().st_size > 0

def test_process_bulk_job_complete(db_session, tmp_path, monkeypatch):
    """Test process_bulk_job background task processing a complete job."""
    monkeypatch.setattr("app.services.job_processor.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("app.services.certificate_generator.settings.OUTPUT_DIR", tmp_path)

    job = Job(event_name="Cloud Computing", event_date="2026-10-09", total_count=2, status="pending")
    db_session.add(job)
    db_session.flush()

    cert1 = Certificate(job_id=job.id, recipient_name="User One", recipient_email="one@example.com", status="pending")
    cert2 = Certificate(job_id=job.id, recipient_name="User Two", recipient_email="two@example.com", status="pending")
    db_session.add_all([cert1, cert2])
    db_session.commit()

    # Execute background worker synchronously
    process_bulk_job(job.id)

    db_session.refresh(job)
    assert job.status == "completed"
    assert job.successful_count == 2
    assert job.failed_count == 0
    assert job.completed_at is not None

    db_session.refresh(cert1)
    db_session.refresh(cert2)
    assert cert1.status == "success"
    assert cert2.status == "success"
    assert cert1.file_path is not None
    assert cert2.file_path is not None

def test_process_bulk_job_individual_failure_resilience(db_session, tmp_path, monkeypatch):
    """
    Test that an individual certificate failure does NOT block other recipients,
    and updates job status to 'completed_with_errors'.
    """
    monkeypatch.setattr("app.services.job_processor.SessionLocal", TestingSessionLocal)

    job = Job(event_name="Resilience Test", event_date="2026-10-09", total_count=2, status="pending")
    db_session.add(job)
    db_session.flush()

    cert_fail = Certificate(job_id=job.id, recipient_name="Failing Recipient", recipient_email="fail@example.com", status="pending")
    cert_pass = Certificate(job_id=job.id, recipient_name="Passing Recipient", recipient_email="pass@example.com", status="pending")
    db_session.add_all([cert_fail, cert_pass])
    db_session.commit()

    # Mock generate_certificate_pdf to raise an error for Failing Recipient
    def mock_generator(certificate_id, recipient_name, event_name, completion_date, **kwargs):
        if recipient_name == "Failing Recipient":
            raise RuntimeError("Simulated PDF generation error")
        return f"generated/{certificate_id}.pdf"

    monkeypatch.setattr("app.services.job_processor.generate_certificate_pdf", mock_generator)

    # Run background worker
    process_bulk_job(job.id)

    db_session.refresh(job)
    assert job.status == "completed_with_errors"
    assert job.successful_count == 1
    assert job.failed_count == 1

    db_session.refresh(cert_fail)
    db_session.refresh(cert_pass)

    assert cert_fail.status == "failed"
    assert "Simulated PDF generation error" in cert_fail.error_message

    assert cert_pass.status == "success"
    assert cert_pass.file_path == f"generated/{cert_pass.id}.pdf"
