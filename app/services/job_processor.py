import logging
from datetime import datetime, timezone
from app.database import SessionLocal
from app.models import Job, Certificate
from app.services.certificate_generator import generate_certificate_pdf

logger = logging.getLogger(__name__)

def process_bulk_job(job_id: str) -> None:
    """
    Background worker function that processes all certificates for a bulk job.
    
    Opens a separate database session to ensure safety and isolation from the
    original HTTP request-scoped session.
    """
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database for background processing.")
            return

        # Update job status to processing
        job.status = "processing"
        db.commit()

        # Fetch all pending certificates for this job
        certificates = db.query(Certificate).filter(Certificate.job_id == job_id).all()

        for cert in certificates:
            cert.status = "processing"
            db.commit()

            try:
                # Generate PDF
                relative_path = generate_certificate_pdf(
                    certificate_id=cert.id,
                    recipient_name=cert.recipient_name,
                    event_name=job.event_name,
                    completion_date=job.event_date
                )
                
                # Success state
                cert.status = "success"
                cert.file_path = relative_path
                cert.error_message = None
                job.successful_count += 1
                logger.info(f"Successfully generated certificate {cert.id} for {cert.recipient_name}")

            except Exception as exc:
                # Individual certificate failure - isolated to avoid stopping job
                logger.exception(f"Failed to generate certificate {cert.id} for {cert.recipient_name}: {exc}")
                cert.status = "failed"
                cert.error_message = f"Certificate generation failed: {str(exc)}"
                job.failed_count += 1

            # Save status for this recipient immediately
            db.commit()

        # Update final job terminal status
        if job.failed_count == 0:
            job.status = "completed"
        elif job.successful_count == 0:
            job.status = "failed"
        else:
            job.status = "completed_with_errors"

        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Completed job {job.id} with status '{job.status}'. Success: {job.successful_count}, Failed: {job.failed_count}")

    except Exception as e:
        logger.exception(f"Unhandled error in background job processor for job {job_id}: {e}")
        db.rollback()
    finally:
        db.close()
