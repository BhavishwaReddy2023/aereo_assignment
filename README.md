# Bulk Certificate Generator Backend

A backend API for generating bulk PDF certificates asynchronously.

---

## 1. How to Set Up the Project

### Prerequisites
- Python 3.10+
- pip

### Setup Steps

1. **Clone or navigate to the project directory:**
   
   be in the root folder "aereo_assignment"

2. **Create and activate a virtual environment:**
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\activate

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

---

## 2. How to Run the Application

Start the FastAPI application with Uvicorn:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once running:
- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

---

## 3. How to Run Tests

Run the test suite using pytest:

```bash
pytest -v
```

All unit and integration tests run in-memory and verify request validation, background processing, failure resilience, and certificate retrieval.

---

## 4. How to Submit a Certificate Generation Request

Submit a `POST` request to `/jobs` with the event details and recipient list.

### Endpoint
`POST /jobs`

### Request Body
```json
{
  "event_name": "Full Stack Backend Engineering Bootcamp",
  "event_date": "October 9, 2026",
  "recipients": [
    {
      "name": "Bhavishwa Puli",
      "email": "bhavishwapuli@example.com"
    },
    {
      "name": "Tharun Reddy",
      "email": "tharun@example.com"
    }
  ]
}
```

### Example (cURL / Bash)
```bash
curl -X POST "http://127.0.0.1:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Full Stack Backend Engineering Bootcamp",
    "event_date": "October 9, 2026",
    "recipients": [
      {"name": "Bhavishwa Puli", "email": "bhavishwapuli@example.com"}
    ]
  }'
```

### Example (PowerShell)
```powershell
$body = @{
    event_name = "Full Stack Backend Engineering Bootcamp"
    event_date = "October 9, 2026"
    recipients = @(
        @{ name = "Bhavishwa Puli"; email = "bhavishwapuli@example.com" }
    )
} | ConvertTo-Json -Depth 5

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/jobs" -Method Post -ContentType "application/json" -Body $body
$response | ConvertTo-Json
```

### Response (`202 Accepted`)
```json
{
  "id": "e4a8b2d1-9f3c-4e8a-b1d5-7c2e9a3f4b5d",
  "job_id": "e4a8b2d1-9f3c-4e8a-b1d5-7c2e9a3f4b5d",
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

## 5. How to Retrieve Generated Certificates

### Option A: Check a Specific Job's Status & Certificate IDs
`GET /jobs/{job_id}`

- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/jobs/<job_id>"
  ```
- **PowerShell**:
  ```powershell
  Invoke-RestMethod -Uri "http://127.0.0.1:8000/jobs/$($response.job_id)" -Method Get | ConvertTo-Json
  ```

Returns the job progress, status, and download links for each certificate in that job.

### Option B: List All Jobs in the Database
`GET /jobs`

- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/jobs"
  ```
- **PowerShell**:
  ```powershell
  Invoke-RestMethod -Uri "http://127.0.0.1:8000/jobs" -Method Get | ConvertTo-Json
  ```

### Option C: List All Certificates Across All Jobs
`GET /certificates`

- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/certificates"
  ```
- **PowerShell**:
  ```powershell
  Invoke-RestMethod -Uri "http://127.0.0.1:8000/certificates" -Method Get | ConvertTo-Json
  ```

### Option D: Download an Individual Certificate PDF
`GET /certificates/{certificate_id}`

- **cURL**:
  ```bash
  curl -O "http://127.0.0.1:8000/certificates/<certificate_id>"
  ```
- **PowerShell**:
  ```powershell
  Invoke-WebRequest -Uri "http://127.0.0.1:8000/certificates/<certificate_id>" -OutFile "certificate.pdf"
  ```

- Streams the generated PDF binary (`Content-Type: application/pdf`).
- Returns `400 Bad Request` if the certificate is not yet ready or failed.
- Returns `404 Not Found` if the ID does not exist or the file is missing.

---

## 6. Important Implementation / Design Decisions

1. **Asynchronous Background Processing**:
   - Uses FastAPI's `BackgroundTasks` to quickly return `202 Accepted` while rendering PDFs in the background without blocking API requests.

2. **Failure Isolation**:
   - Each recipient's certificate generation is wrapped in an isolated try-catch block.
   - If an individual certificate fails, its error is recorded, and the process continues with the remaining recipients.
   - Overall job status reflects partial failures (`completed_with_errors`) instead of failing the entire batch.

3. **Dual PDF Rendering Engine**:
   - Primary engine is **WeasyPrint** for HTML/CSS rendering.
   - Seamlessly falls back to **xhtml2pdf** on environments where GTK3 system libraries are unavailable (e.g., standard Windows setups), ensuring zero setup friction.

4. **Thread-Safe Database Sessions**:
   - SQLite with SQLAlchemy ORM.
   - Background workers open a separate, isolated database session (`SessionLocal`) to ensure thread safety and prevent connection leaks.

5. **Dynamic Name Font Scaling**:
   - Font sizes for recipient names automatically scale based on string length (from 36px down to 18px) to prevent long names from wrapping awkwardly, clipping, or overflowing the certificate borders.
   