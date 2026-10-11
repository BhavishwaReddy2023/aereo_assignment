import pytest
from app.models import Job, Certificate

def test_download_unknown_certificate(client):
    """Test 404 when downloading a non-existent certificate ID."""
    response = client.get("/certificates/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_download_failed_certificate(client, db_session):
    """Test 400 Bad Request when requesting a certificate marked as failed."""
    job = Job(event_name="Test Event", event_date="2026-10-09", total_count=1)
    db_session.add(job)
    db_session.flush()

    cert = Certificate(
        job_id=job.id,
        recipient_name="Failed User",
        recipient_email="failed@example.com",
        status="failed",
        error_message="Font rendering engine error"
    )
    db_session.add(cert)
    db_session.commit()

    response = client.get(f"/certificates/{cert.id}")
    assert response.status_code == 400
    assert "failed" in response.json()["detail"].lower()
    assert "Font rendering engine error" in response.json()["detail"]

def test_download_pending_certificate(client, db_session):
    """Test 400 Bad Request when requesting a certificate still pending."""
    job = Job(event_name="Test Event", event_date="2026-10-09", total_count=1)
    db_session.add(job)
    db_session.flush()

    cert = Certificate(
        job_id=job.id,
        recipient_name="Pending User",
        recipient_email="pending@example.com",
        status="pending"
    )
    db_session.add(cert)
    db_session.commit()

    response = client.get(f"/certificates/{cert.id}")
    assert response.status_code == 400
    assert "pending" in response.json()["detail"].lower()

def test_download_missing_file_on_disk(client, db_session):
    """Test 404 Not Found when certificate is marked success but PDF file was deleted."""
    job = Job(event_name="Test Event", event_date="2026-10-09", total_count=1)
    db_session.add(job)
    db_session.flush()

    cert = Certificate(
        job_id=job.id,
        recipient_name="Ghost File User",
        recipient_email="ghost@example.com",
        status="success",
        file_path="generated/non_existent_file.pdf"
    )
    db_session.add(cert)
    db_session.commit()

    response = client.get(f"/certificates/{cert.id}")
    assert response.status_code == 404
    assert "not found on server disk" in response.json()["detail"].lower()

def test_download_successful_certificate(client, db_session, tmp_path, monkeypatch):
    """Test successful PDF download when file exists."""
    # Create fake PDF file in temporary directory
    fake_pdf = tmp_path / "cert_test.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4 Fake PDF Content")

    job = Job(event_name="Test Event", event_date="2026-10-09", total_count=1)
    db_session.add(job)
    db_session.flush()

    cert = Certificate(
        job_id=job.id,
        recipient_name="Valid Recipient",
        recipient_email="valid@example.com",
        status="success",
        file_path=str(fake_pdf)
    )
    db_session.add(cert)
    db_session.commit()

    response = client.get(f"/certificates/{cert.id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert b"%PDF-1.4 Fake PDF Content" in response.content

def test_list_all_certificates(client, db_session):
    """Test fetching all certificates across all jobs."""
    job = Job(event_name="Global Summit", event_date="2026-10-10", total_count=1)
    db_session.add(job)
    db_session.flush()

    cert = Certificate(
        job_id=job.id,
        recipient_name="George Clark",
        recipient_email="george@example.com",
        status="pending"
    )
    db_session.add(cert)
    db_session.commit()

    response = client.get("/certificates")
    assert response.status_code == 200
    certs = response.json()
    assert isinstance(certs, list)
    assert len(certs) >= 1
    assert "certificate_id" in certs[0]
    assert "id" in certs[0]
    assert "recipient_name" in certs[0]
