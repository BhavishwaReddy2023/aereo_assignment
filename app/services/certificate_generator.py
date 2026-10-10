import os
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.config import settings

logger = logging.getLogger(__name__)

# Set up Jinja2 environment with autoescape enabled for HTML safety
env = Environment(
    loader=FileSystemLoader(str(settings.TEMPLATE_DIR)),
    autoescape=select_autoescape(['html', 'xml'])
)

def calculate_name_font_size(name: str) -> int:
    """Dynamically adjust font size based on recipient name length."""
    length = len(name)
    if length <= 20:
        return 36
    elif length <= 35:
        return 28
    elif length <= 50:
        return 22
    else:
        return 18

def generate_certificate_pdf(
    certificate_id: str,
    recipient_name: str,
    event_name: str,
    completion_date: str,
    output_dir: Path = settings.OUTPUT_DIR
) -> str:
    """
    Renders Jinja2 HTML certificate template and converts it to PDF.
    
    Returns:
        str: Relative path to the generated PDF file.
    
    Raises:
        RuntimeError: If PDF generation fails.
    """
    # Render HTML template with recipient data
    font_size = calculate_name_font_size(recipient_name)
    template = env.get_template("certificate.html")
    rendered_html = template.render(
        recipient_name=recipient_name,
        event_name=event_name,
        completion_date=completion_date,
        certificate_id=certificate_id,
        name_font_size=font_size
    )

    filename = f"{certificate_id}.pdf"
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / filename

    generated = False
    last_error = None

    try:
        from weasyprint import HTML
        HTML(string=rendered_html).write_pdf(target=str(file_path))
        generated = True
        logger.info(f"Certificate PDF generated via WeasyPrint: {file_path}")
    except (ImportError, Exception) as e:
        last_error = str(e)
        logger.warning(f"WeasyPrint rendering unavailable/failed: {e}. Falling back to xhtml2pdf.")

    # Fallback to xhtml2pdf if WeasyPrint failed or was unavailable
    if not generated:
        try:
            from xhtml2pdf import pisa
            with open(file_path, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(rendered_html, dest=pdf_file)
                if pisa_status.err:
                    raise RuntimeError(f"xhtml2pdf error status: {pisa_status.err}")
            generated = True
            logger.info(f"Certificate PDF generated via xhtml2pdf: {file_path}")
        except Exception as e:
            last_error = str(e)
            logger.error(f"xhtml2pdf rendering failed: {e}")

    if not generated or not file_path.exists():
        raise RuntimeError(f"Failed to generate certificate PDF. Cause: {last_error}")

    # Return relative path for database storage if under CWD, else string path
    try:
        relative_path = str(file_path.relative_to(Path.cwd()))
    except ValueError:
        relative_path = str(file_path)
    return relative_path
