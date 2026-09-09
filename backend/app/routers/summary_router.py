from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.document_schema import DocumentResponse
from app.services.llm_service import generate_medical_summary

router = APIRouter(prefix="/summary", tags=["Summary"])


@router.post("/generate/{document_id}", response_model=DocumentResponse)
def generate_summary(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generates an AI plain-language summary for a document the user owns."""
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    if not document.ocr_text or not document.ocr_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This document has no extracted text to summarize.",
        )

    try:
        summary = generate_medical_summary(document.ocr_text)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to generate summary right now. Please try again.",
        )

    document.ai_summary = summary
    db.commit()
    db.refresh(document)

    return document