from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Certificate
from app.schemas import CertificateResponse

router = APIRouter(prefix="/certificates", tags=["Certificates"])

@router.get("", response_model=List[CertificateResponse])
def get_all_certificates(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    GET /certificates: Return all certificates across all jobs in the database.
    """
    certs = db.query(Certificate).order_by(Certificate.created_at.desc()).all()
    results = []
    for cert in certs:
        download_url = None
        if cert.status == "success" and cert.file_path:
            download_url = str(request.url_for("download_certificate", certificate_id=cert.id))
        results.append(
            CertificateResponse(
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
        )
    return results

@router.get("/{certificate_id}", name="download_certificate")
def download_certificate(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    """
    GET /certificates/{certificate_id}: Return generated PDF certificate for download.
    """
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' not found."
        )

    if cert.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate generation failed for recipient '{cert.recipient_name}'. Error: {cert.error_message}"
        )

    if cert.status in ("pending", "processing"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate is still in '{cert.status}' status. Please try again shortly."
        )

    if cert.status != "success" or not cert.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate is not ready for download. Current status: '{cert.status}'."
        )

    # Check physical file existence on disk
    file_path = Path(cert.file_path)
    if not file_path.is_absolute():
        file_path = Path.cwd() / file_path

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate file for ID '{certificate_id}' was not found on server disk."
        )

    # Safe filename for download header
    safe_recipient = "".join(c for c in cert.recipient_name if c.isalnum() or c in (" ", "_", "-")).strip()
    safe_filename = f"Certificate_{safe_recipient}_{certificate_id[:8]}.pdf".replace(" ", "_")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=safe_filename
    )
