import pytest
from app.config import settings

def test_create_job_valid(client):
    """Test creating a valid bulk certificate job."""
    payload = {
        "event_name": "Python Masters Bootcamp",
        "event_date": "2026-10-09",
        "recipients": [
            {"name": "Alice Smith", "email": "alice@example.com"},
            {"name": "Bob Jones", "email": "bob@example.com"}
        ]
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert data["event_name"] == "Python Masters Bootcamp"
    assert data["total_count"] == 2
    assert data["status"] in ("pending", "processing", "completed")

def test_create_job_invalid_email(client):
    """Test payload validation for malformed recipient email."""
    payload = {
        "event_name": "Python Bootcamp",
        "event_date": "2026-10-09",
        "recipients": [
            {"name": "Alice Smith", "email": "not-an-email"}
        ]
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("email" in str(e["loc"]) for e in errors)

def test_create_job_empty_name(client):
    """Test payload validation for empty recipient name."""
    payload = {
        "event_name": "Python Bootcamp",
        "event_date": "2026-10-09",
        "recipients": [
            {"name": "   ", "email": "alice@example.com"}
        ]
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422

def test_create_job_empty_recipients_list(client):
    """Test payload validation for empty recipient list."""
    payload = {
        "event_name": "Python Bootcamp",
        "event_date": "2026-10-09",
        "recipients": []
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422

def test_create_job_missing_event_name(client):
    """Test payload validation when event_name is missing."""
    payload = {
        "event_date": "2026-10-09",
        "recipients": [
            {"name": "Alice Smith", "email": "alice@example.com"}
        ]
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422

def test_get_job_status(client):
    """Test fetching job status and details."""
    payload = {
        "event_name": "Web Dev Workshop",
        "event_date": "2026-10-09",
        "recipients": [
            {"name": "Charlie Brown", "email": "charlie@example.com"}
        ]
    }
    create_res = client.post("/jobs", json=payload)
    job_id = create_res.json()["id"]

    get_res = client.get(f"/jobs/{job_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == job_id
    assert len(data["certificates"]) == 1
    assert data["certificates"][0]["recipient_name"] == "Charlie Brown"

def test_get_non_existent_job(client):
    """Test 404 response for unknown job ID."""
    response = client.get("/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_get_job_certificates(client):
    """Test fetching list of certificates for a job."""
    payload = {
        "event_name": "AI Summit",
        "event_date": "2026-10-09",
        "recipients": [
            {"name": "David Miller", "email": "david@example.com"}
        ]
    }
    create_res = client.post("/jobs", json=payload)
    job_id = create_res.json()["id"]

    certs_res = client.get(f"/jobs/{job_id}/certificates")
    assert certs_res.status_code == 200
    certs = certs_res.json()
    assert len(certs) == 1
    assert certs[0]["recipient_email"] == "david@example.com"
