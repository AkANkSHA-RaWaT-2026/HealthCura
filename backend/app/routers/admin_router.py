from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.models.document import Document
from app.models.health_record import HealthRecord
from app.models.chat_message import ChatMessage
from app.schemas.admin_schema import AdminStats, PatientSummary
from app.services.llm_service import generate_discharge_summary
from app.services.pdf_service import build_discharge_pdf

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=AdminStats)
def get_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Returns aggregate platform statistics. Admin only."""
    total_patients = db.query(User).filter(User.role == "patient").count()
    total_documents = db.query(Document).count()
    total_health_records = db.query(HealthRecord).count()
    total_chat_messages = db.query(ChatMessage).count()

    return AdminStats(
        total_patients=total_patients,
        total_documents=total_documents,
        total_health_records=total_health_records,
        total_chat_messages=total_chat_messages,
    )


@router.get("/patients", response_model=list[PatientSummary])
def list_patients(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Returns all patients with their document counts. Admin only."""
    results = (
        db.query(
            User.id,
            User.full_name,
            User.email,
            User.created_at,
            func.count(Document.id).label("document_count"),
        )
        .outerjoin(Document, Document.user_id == User.id)
        .filter(User.role == "patient")
        .group_by(User.id)
        .order_by(User.created_at.desc())
        .all()
    )

    return [
        PatientSummary(
            id=r.id,
            full_name=r.full_name,
            email=r.email,
            document_count=r.document_count,
            created_at=r.created_at,
        )
        for r in results
    ]


@router.post("/export/{patient_id}")
def export_patient_report(
    patient_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Generates a PDF health summary for a specific patient. Admin only."""
    patient = db.query(User).filter(User.id == patient_id, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    documents = db.query(Document).filter(Document.user_id == patient_id).all()
    if not documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This patient has no documents to summarize.",
        )

    parts = []
    for doc in documents:
        section = f"--- Document: {doc.original_filename} ({doc.document_type or 'Unclassified'}) ---\n"
        section += doc.ai_summary or (doc.ocr_text or "")[:500]
        parts.append(section)

    records = db.query(HealthRecord).filter(HealthRecord.user_id == patient_id).all()
    if records:
        parts.append("--- Health Metrics ---")
        for r in records:
            status_note = f" ({r.status})" if r.status and r.status != "unknown" else ""
            parts.append(f"{r.metric_name}: {r.value} {r.unit or ''}{status_note}")

    context = "\n\n".join(parts)

    try:
        summary_text = generate_discharge_summary(patient.full_name, context)
        pdf_path = build_discharge_pdf(patient.full_name, patient.email, summary_text)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to generate report right now. Please try again.",
        )

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"HealthCura_Report_{patient.full_name.replace(' ', '_')}.pdf",
    )