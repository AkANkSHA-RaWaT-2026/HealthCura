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

router = APIRouter(prefix="/documents", tags=["Documents"])

# Security limits - prevents abuse and keeps within Cloudinary free tier
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a medical document (image or PDF). Requires login."""

    # Validate file extension
    _, extension = os.path.splitext(file.filename)
    extension = extension.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Accepted types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file into memory to check size (FastAPI doesn't expose size upfront)
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

    # Save to a temp file - Cloudinary's SDK expects a file path, not raw bytes
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        file_url = upload_file_to_cloudinary(tmp_path)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to upload file. Please try again.",
        )
    finally:
        # Always clean up the temp file, even if upload failed
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    file_type = "pdf" if extension == ".pdf" else "image"

    new_document = Document(
        user_id=current_user.id,
        original_filename=file.filename,
        file_url=file_url,
        file_type=file_type,
        ocr_status="pending",
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

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