"""Summary routes: generates a blood report summary and returns it with flagged results."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.document import Document
from app.models.health_record import HealthRecord
from app.models.user import User
from app.schemas.summary_schema import SummaryResponse
from app.services.summary_service import DISCLAIMER, build_flagged, create_summary

router = APIRouter(prefix="/summary", tags=["Summary"])


def load_owned_document(db: Session, document_id: int, user_id: int) -> Document:
    """Returns the document if the user owns it, otherwise raises 404."""
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == user_id)
        .first()
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    return document


def load_health_rows(db: Session, document_id: int, user_id: int) -> list[dict]:
    """Returns the document's health records as plain dictionaries."""
    records = (
        db.query(HealthRecord)
        .filter(HealthRecord.document_id == document_id, HealthRecord.user_id == user_id)
        .order_by(HealthRecord.id)
        .all()
    )
    return [
        {
            "metric_name": record.metric_name,
            "value": record.value,
            "unit": record.unit,
            "status": record.status,
            "printed_low": record.printed_low,
            "printed_high": record.printed_high,
        }
        for record in records
    ]


@router.post("/generate/{document_id}", response_model=SummaryResponse)
def generate_summary(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generates a summary for a document the user owns and saves it to the document."""
    document = load_owned_document(db, document_id, current_user.id)

    if not document.ocr_text or not document.ocr_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This document has no extracted text to summarize.",
        )

    rows = load_health_rows(db, document.id, current_user.id)
    result = create_summary(rows, document.document_type or "Other")

    try:
        document.ai_summary = result["summary"]
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save the summary. Please try again.",
        )

    return SummaryResponse(document_id=document.id, **result)


@router.get("/{document_id}", response_model=SummaryResponse)
def get_saved_summary(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the saved summary with flagged results. Does not call the language model."""
    document = load_owned_document(db, document_id, current_user.id)

    if not document.ai_summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No summary has been generated for this document yet.",
        )

    rows = load_health_rows(db, document.id, current_user.id)
    return SummaryResponse(
        document_id=document.id,
        document_type=document.document_type or "Other",
        summary=document.ai_summary,
        flagged=build_flagged(rows),
        disclaimer=DISCLAIMER,
        summary_source="saved",
    )