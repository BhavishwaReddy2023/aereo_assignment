# Bulk Certificate Generator Backend

A robust, production-ready Python backend API built with FastAPI, SQLAlchemy (SQLite), Jinja2, and WeasyPrint / xhtml2pdf. The system accepts bulk certificate requests containing multiple recipients, validates input data, generates individual landscape PDF certificates asynchronously in the background, tracks job progress, insulates against individual certificate failures, and serves downloadable PDF certificates.

---

## 1. Architecture Overview

The system follows a clean modular service-oriented architecture:

```
bulk-certificate-generator/
│
├── app/
│   ├── main.py                   # FastAPI application initialization & middleware
│   ├── config.py                 # Centralized configuration & environment settings
│   ├── database.py               # SQLAlchemy engine, session maker, & get_db dependency
│   ├── models.py                 # ORM Database models (Job & Certificate)
│   ├── schemas.py                # Pydantic schemas for request validation & responses
│   ├── routes/
│   │   ├── jobs.py               # POST /jobs, GET /jobs/{job_id}, GET /jobs/{job_id}/certificates
│   │   └── certificates.py       # GET /certificates/{certificate_id}
│   ├── services/
│   │   ├── certificate_generator.py # Jinja2 HTML rendering & HTML-to-PDF conversion
│   │   └── job_processor.py         # Asynchronous background job worker
│   └── templates/
│       └── certificate.html      # Professional landscape certificate HTML/CSS template
│
├── generated/                    # Local storage directory for generated PDF files
├── tests/
│   ├── conftest.py               # Test fixtures (isolated SQLite DB & temp file storage)
│   ├── test_jobs.py              # API endpoint validation & job routes tests
│   ├── test_certificates.py      # Certificate retrieval & error handling tests
│   └── test_generation.py        # PDF rendering & failure-resilience background tests
├── requirements.txt              # Project dependency manifest
├── .env.example                  # Environment variable reference
└── README.md                     # Comprehensive project documentation
```

### System Architecture Highlights:
- **Request Isolation**: HTTP requests return immediately with `202 Accepted` after database insertion of `Job` and `Certificate` records.
- **Background Worker**: `FastAPI.BackgroundTasks` spawns `process_bulk_job(job_id)` in the background.
- **Session Safety**: The background worker opens a fresh, isolated SQLAlchemy `SessionLocal()` session to prevent concurrency issues and request-session lifecycle leaks.
- **Failure Resilience**: Individual certificate generation errors are caught and recorded. The loop continues processing remaining recipients, leaving the job status as `completed_with_errors` if partial failures occur.
- **Dynamic Text Scaling**: Dynamic font sizing prevents long recipient names from overflowing or being truncated.
- **Dual PDF Engine**: Primary rendering engine is **WeasyPrint**. If system-level GTK libraries are absent (e.g., native Windows environments), the engine seamlessly falls back to **xhtml2pdf**.

---

## 2. Prerequisites & Setup

### Requirements
- **Python**: `3.10` or higher (tested on Python 3.12)
- **Pip**: `pip` 24.0+

### System Dependencies for PDF Generation

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

#### macOS (Homebrew)
```bash
brew install cairo pango gdk-pixbuf libffi
```

#### Windows
WeasyPrint relies on GTK3 libraries (`libgobject-2.0-0`). If GTK3 is not installed via MSYS2 / GTK for Windows, **the application automatically detects the missing library and falls back to `xhtml2pdf` without requiring extra system drivers or breaking runtime execution**.

---

## 3. Installation Guide

### Step 1: Clone or Navigate to Project Directory
```bash
cd c:/coding/aereo_assignment
```

### Step 2: Create Virtual Environment
```bash
# On Windows (PowerShell)
python -m venv venv
.\venv\Scripts\activate

# On Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default configuration values:
```env
APP_NAME="Bulk Certificate Generator Backend"
DATABASE_URL="sqlite:///./certificates.db"
OUTPUT_DIR="generated"
TEMPLATE_DIR="app/templates"
MAX_RECIPIENTS_PER_REQUEST=1000
```

---

## 4. Running the Application

Start the FastAPI development server with Uvicorn:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once running:
- **Swagger Interactive UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 5. Running Automated Tests

Run the full pytest suite:

```bash
pytest -v
```

All 17 automated tests verify request validation, PDF generation, status updates, individual failure resilience, file retrieval, and missing file handling.

---

## 6. API Reference & Usage Examples

### 1. Create Bulk Generation Job
`POST /jobs`

Creates a new job and queues PDF generation for all recipients.

**Sample Request Body:**
```json
{
  "event_name": "Full Stack Backend Engineering Bootcamp",
  "event_date": "October 9, 2026",
  "recipients": [
    {
      "name": "Jane Doe",
      "email": "jane.doe@example.com"
    },
    {
      "name": "Professor Bartholomew Dominick Harrington-Smythe III",
      "email": "bartholomew@example.com"
    },
    {
      "name": "Alice Johnson",
      "email": "alice@example.com"
    }
  ]
}
```

**cURL Example:**
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/jobs' \
  -H 'Content-Type: application/json' \
  -d '{
    "event_name": "Full Stack Backend Engineering Bootcamp",
    "event_date": "October 9, 2026",
    "recipients": [
      {"name": "Jane Doe", "email": "jane.doe@example.com"}
    ]
  }'
```

**PowerShell Example:**
```powershell
$body = @{
    event_name = "Full Stack Backend Engineering Bootcamp"
    event_date = "October 9, 2026"
    recipients = @(
        @{ name = "Jane Doe"; email = "jane.doe@example.com" }
    )
} | ConvertTo-Json -Depth 5

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/jobs" -Method Post -ContentType "application/json" -Body $body
$response | ConvertTo-Json
```

**Response (`202 Accepted`):**
```json
{
  "id": "e4a8b2d1-9f3c-4e8a-b1d5-7c2e9a3f4b5d",
  "event_name": "Full Stack Backend Engineering Bootcamp",
  "event_date": "October 9, 2026",
  "status": "pending",
  "total_count": 1,
  "successful_count": 0,
  "failed_count": 0,
  "pending_count": 1,
  "processing_count": 0,
  "created_at": "2026-10-09T21:20:00.000000Z",
  "completed_at": null
}
```

---

### 2. Get Job Status & Certificate Details
`GET /jobs/{job_id}`

Retrieves overall job progress, recipient counts, and detailed per-certificate status.

**cURL Example:**
```bash
curl -X 'GET' 'http://127.0.0.1:8000/jobs/e4a8b2d1-9f3c-4e8a-b1d5-7c2e9a3f4b5d'
```

**PowerShell Example:**
```powershell
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/jobs/e4a8b2d1-9f3c-4e8a-b1d5-7c2e9a3f4b5d" -Method Get
$response | ConvertTo-Json -Depth 5
```

**Response (`200 OK`):**
```json
{
  "id": "e4a8b2d1-9f3c-4e8a-b1d5-7c2e9a3f4b5d",
  "event_name": "Full Stack Backend Engineering Bootcamp",
  "event_date": "October 9, 2026",
  "status": "completed",
  "total_count": 1,
  "successful_count": 1,
  "failed_count": 0,
  "pending_count": 0,
  "processing_count": 0,
  "created_at": "2026-10-09T21:20:00.000000Z",
  "completed_at": "2026-10-09T21:20:01.500000Z",
  "certificates": [
    {
      "id": "7b2a9f1c-3d4e-5f6a-8b9c-0d1e2f3a4b5c",
      "job_id": "e4a8b2d1-9f3c-4e8a-b1d5-7c2e9a3f4b5d",
      "recipient_name": "Jane Doe",
      "recipient_email": "jane.doe@example.com",
      "status": "success",
      "file_path": "generated/7b2a9f1c-3d4e-5f6a-8b9c-0d1e2f3a4b5c.pdf",
      "download_url": "http://127.0.0.1:8000/certificates/7b2a9f1c-3d4e-5f6a-8b9c-0d1e2f3a4b5c",
      "error_message": null,
      "created_at": "2026-10-09T21:20:00.000000Z"
    }
  ]
}
```

---

### 3. Get Certificates for Job
`GET /jobs/{job_id}/certificates`

Returns certificate records and download links for all recipients in a job.

**cURL Example:**
```bash
curl -X 'GET' 'http://127.0.0.1:8000/jobs/e4a8b2d1-9f3c-4e8a-b1d5-7c2e9a3f4b5d/certificates'
```

**PowerShell Example:**
```powershell
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/jobs/e4a8b2d1-9f3c-4e8a-b1d5-7c2e9a3f4b5d/certificates" -Method Get
$response | ConvertTo-Json -Depth 5
```

**Response (`200 OK`):**
```json
[
  {
    "id": "7b2a9f1c-3d4e-5f6a-8b9c-0d1e2f3a4b5c",
    "job_id": "e4a8b2d1-9f3c-4e8a-b1d5-7c2e9a3f4b5d",
    "recipient_name": "Jane Doe",
    "recipient_email": "jane.doe@example.com",
    "status": "success",
    "file_path": "generated/7b2a9f1c-3d4e-5f6a-8b9c-0d1e2f3a4b5c.pdf",
    "download_url": "http://127.0.0.1:8000/certificates/7b2a9f1c-3d4e-5f6a-8b9c-0d1e2f3a4b5c",
    "error_message": null,
    "created_at": "2026-10-09T21:20:00.000000Z"
  }
]
```

---

### 4. Download Certificate PDF
`GET /certificates/{certificate_id}`

Streams the generated PDF file directly for browser view or file download.

**cURL Example:**
```bash
curl -O 'http://127.0.0.1:8000/certificates/7b2a9f1c-3d4e-5f6a-8b9c-0d1e2f3a4b5c'
```

**PowerShell Example:**
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/certificates/7b2a9f1c-3d4e-5f6a-8b9c-0d1e2f3a4b5c" -OutFile "certificate.pdf"
```

**HTTP Status Behaviors:**
- `200 OK`: Returns binary PDF file (`Content-Type: application/pdf`).
- `404 Not Found`: Certificate ID does not exist, or file missing on disk.
- `400 Bad Request`: Certificate status is `failed`, `pending`, or `processing`.

---

## 7. Status Definitions

### Job Statuses
- `pending`: Job record created, awaiting background worker execution.
- `processing`: Background worker actively generating PDFs.
- `completed`: All certificate PDFs generated successfully (`failed_count == 0`).
- `completed_with_errors`: Job finished, but one or more certificates failed (`successful_count > 0` and `failed_count > 0`).
- `failed`: Job finished with 0 successful certificates (`successful_count == 0`).

### Certificate Statuses
- `pending`: Record created, awaiting rendering.
- `processing`: PDF rendering currently in progress.
- `success`: PDF generated and saved successfully to disk.
- `failed`: Rendering or disk write failed; `error_message` contains sanitized failure reason.

---

## 8. Design Decisions & Limitations

1. **Background Tasks Approach**:
   - Built using FastAPI's standard `BackgroundTasks` runner to avoid heavy external dependencies (Redis, Celery, RabbitMQ) as specified by assignment scope.
   - **Limitation**: `BackgroundTasks` runs in-process. If the Uvicorn server restarts or crashes during processing, tasks currently executing in memory will be interrupted. There is no durable job persistence broker.

2. **Database Concurrency**:
   - SQLite is used with `check_same_thread=False` and isolated `SessionLocal()` instances inside background tasks.
   - For multi-process horizontal scaling (e.g. multi-node deployment), PostgreSQL with Celery/Redis is recommended.

3. **PDF Generation Dual-Engine**:
   - HTML/CSS rendered using Jinja2 with strict autoescape (`select_autoescape(['html', 'xml'])`).
   - WeasyPrint provides high-fidelity CSS landscape rendering. Automatic fallback to `xhtml2pdf` ensures zero-breakage on Windows setups missing C GTK libraries.
