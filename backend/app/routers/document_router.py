import os
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.document_schema import DocumentResponse
from app.services.cloudinary_service import upload_file_to_cloudinary
from app.services.ocr_service import extract_text_from_image_path, extract_text_from_pdf
from app.models.health_record import HealthRecord
from app.services.health_extraction_service import extract_health_metrics
from app.services.reference_ranges import get_status

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a medical document (image or PDF), extract text via OCR,
    and store both the file (Cloudinary) and extracted text (DB).
    Requires login.
    """
    _, extension = os.path.splitext(file.filename)
    extension = extension.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Accepted types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB.",
        )
    if len(file_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        # Run OCR first - if this fails, we don't want a half-saved document
        if extension == ".pdf":
            extracted_text = extract_text_from_pdf(tmp_path)
        else:
            extracted_text = extract_text_from_image_path(tmp_path)

        file_url = upload_file_to_cloudinary(tmp_path)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to process the uploaded document. Please try a different file.",
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    file_type = "pdf" if extension == ".pdf" else "image"

    new_document = Document(
        user_id=current_user.id,
        original_filename=file.filename,
        file_url=file_url,
        file_type=file_type,
        ocr_status="completed",
        ocr_text=extracted_text,
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

     # Best-effort extraction of structured health metrics from OCR text
    extracted_metrics = extract_health_metrics(extracted_text)
    for metric in extracted_metrics:
        health_record = HealthRecord(
            user_id=current_user.id,
            document_id=new_document.id,
            metric_name=metric["metric_name"],
            value=metric["value"],
            unit=metric["unit"],
            recorded_date=metric["recorded_date"],
            status=get_status(metric["metric_name"], metric["value"]),
        )
        db.add(health_record)
    db.commit()
    
    return new_document

    


@router.get("/", response_model=list[DocumentResponse])
def list_my_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns all documents uploaded by the currently logged-in user."""
    documents = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns a single document - only if it belongs to the current user."""
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
    return document

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deletes a document - only if it belongs to the current user."""
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

    db.delete(document)
    db.commit()