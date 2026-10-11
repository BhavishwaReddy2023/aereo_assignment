from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job, Certificate
from app.schemas import (
    JobCreateRequest,
    JobSummaryResponse,
    JobDetailResponse,
    CertificateResponse
)
from app.services.job_processor import process_bulk_job

router = APIRouter(prefix="/jobs", tags=["Jobs"])

def build_certificate_response(cert: Certificate, request: Request) -> CertificateResponse:
    """Helper to add dynamic download URL to CertificateResponse."""
    download_url = None
    if cert.status == "success" and cert.file_path:
        # Build absolute download URL using request base URL
        download_url = str(request.url_for("download_certificate", certificate_id=cert.id))
    
    return CertificateResponse(
        id=cert.id,
        certificate_id=cert.id,
        job_id=cert.job_id,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        status=cert.status,
        file_path=cert.file_path,
        download_url=download_url,
        error_message=cert.error_message,
        created_at=cert.created_at
    )

def build_job_detail_response(job: Job, request: Request) -> JobDetailResponse:
    """Helper to construct JobDetailResponse with calculated pending/processing counts."""
    certificates = job.certificates or []
    pending_count = sum(1 for c in certificates if c.status == "pending")
    processing_count = sum(1 for c in certificates if c.status == "processing")
    
    cert_responses = [build_certificate_response(c, request) for c in certificates]
    
    return JobDetailResponse(
        id=job.id,
        job_id=job.id,
        event_name=job.event_name,
        event_date=job.event_date,
        status=job.status,
        total_count=job.total_count,
        successful_count=job.successful_count,
        failed_count=job.failed_count,
        pending_count=pending_count,
        processing_count=processing_count,
        created_at=job.created_at,
        completed_at=job.completed_at,
        certificates=cert_responses
    )

@router.get("", response_model=List[JobSummaryResponse])
def get_all_jobs(
    db: Session = Depends(get_db)
):
    """
    GET /jobs: Return all jobs in the database.
    """
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    results = []
    for job in jobs:
        certificates = job.certificates or []
        pending_count = sum(1 for c in certificates if c.status == "pending")
        processing_count = sum(1 for c in certificates if c.status == "processing")
        results.append(
            JobSummaryResponse(
                id=job.id,
                job_id=job.id,
                event_name=job.event_name,
                event_date=job.event_date,
                status=job.status,
                total_count=job.total_count,
                successful_count=job.successful_count,
                failed_count=job.failed_count,
                pending_count=pending_count,
                processing_count=processing_count,
                created_at=job.created_at,
                completed_at=job.completed_at
            )
        )
    return results

@router.post("", response_model=JobSummaryResponse, status_code=status.HTTP_202_ACCEPTED)
def create_bulk_job(
    payload: JobCreateRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    POST /jobs: Accept bulk certificate generation request.
    Validates payload, creates Job and Certificate records, and schedules background processing.
    """
    # Create Job record
    job = Job(
        event_name=payload.event_name,
        event_date=payload.event_date,
        status="pending",
        total_count=len(payload.recipients),
        successful_count=0,
        failed_count=0
    )
    db.add(job)
    db.flush()

    # Create Certificate records
    for recipient in payload.recipients:
        cert = Certificate(
            job_id=job.id,
            recipient_name=recipient.name,
            recipient_email=recipient.email,
            status="pending"
        )
        db.add(cert)

    db.commit()
    db.refresh(job)

    # Queue background generation task
    background_tasks.add_task(process_bulk_job, job.id)

    return JobSummaryResponse(
        id=job.id,
        job_id=job.id,
        event_name=job.event_name,
        event_date=job.event_date,
        status=job.status,
        total_count=job.total_count,
        successful_count=job.successful_count,
        failed_count=job.failed_count,
        pending_count=job.total_count,
        processing_count=0,
        created_at=job.created_at,
        completed_at=job.completed_at
    )

@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job_status(
    job_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    GET /jobs/{job_id}: Return job status, counts, and individual certificate results.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )
    return build_job_detail_response(job, request)

@router.get("/{job_id}/certificates", response_model=List[CertificateResponse])
def get_job_certificates(
    job_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    GET /jobs/{job_id}/certificates: Return certificate records and statuses for a job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )
    return [build_certificate_response(c, request) for c in job.certificates]
