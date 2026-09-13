from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
import tempfile
import os

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.health_record import HealthRecord
from app.services.llm_service import generate_discharge_summary
from app.services.pdf_service import build_discharge_pdf

router = APIRouter(prefix="/discharge", tags=["Discharge Summary"])


def _gather_patient_context(db: Session, user: User) -> str:
    """Combines all of a patient's document summaries and health records into one text block for the LLM."""
    documents = (
        db.query(Document)
        .filter(Document.user_id == user.id)
        .order_by(Document.created_at.asc())
        .all()
    )

    if not documents:
        return ""

    parts = []
    for doc in documents:
        doc_section = f"--- Document: {doc.original_filename} ({doc.document_type or 'Unclassified'}, {doc.created_at.date()}) ---\n"
        if doc.ai_summary:
            doc_section += f"Summary: {doc.ai_summary}\n"
        elif doc.ocr_text:
            # Fall back to raw OCR text if no summary was generated for this document yet
            doc_section += f"Extracted text: {doc.ocr_text[:500]}\n"
        parts.append(doc_section)

    records = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == user.id)
        .order_by(HealthRecord.recorded_date.asc().nulls_last())
        .all()
    )
    if records:
        parts.append("--- Health Metrics ---")
        for r in records:
            status_note = f" ({r.status})" if r.status and r.status != "unknown" else ""
            parts.append(f"{r.metric_name}: {r.value} {r.unit or ''}{status_note}")

    return "\n\n".join(parts)


@router.post("/generate")
def generate_discharge_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generates a downloadable PDF discharge-style summary from the patient's document history."""
    context = _gather_patient_context(db, current_user)

    if not context:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents found. Upload at least one document before generating a summary.",
        )

    try:
        summary_text = generate_discharge_summary(current_user.full_name, context)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to generate summary right now. Please try again.",
        )

    try:
        pdf_path = build_discharge_pdf(current_user.full_name, current_user.email, summary_text)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create the PDF. Please try again.",
        )

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="HealthCura_Summary.pdf",
    )