"""Document upload, OCR, and blood report classification routes."""

import logging
import os
import re
import tempfile

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.health_record import HealthRecord
from app.models.user import User
from app.schemas.document_schema import DocumentResponse
from app.services.blood_report_parser import parse_blood_report
from app.services.cloudinary_service import upload_file_to_cloudinary
from app.services.embedding_service import chunk_text, embed_texts
from app.services.ocr_service import extract_text_from_image_path, extract_text_from_pdf
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_FILENAME_LENGTH = 120
BLOOD_REPORT_TYPE = "Blood Test Report"

# Signatures of the real file types. The type is read from the content,
# not from the file name, so a renamed file is still identified correctly.
FILE_SIGNATURES = {
    "pdf": b"%PDF",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpeg": b"\xff\xd8\xff",
}

# Temporary file extension for each type, so OCR tools open the file correctly
TEMP_SUFFIX = {"pdf": ".pdf", "png": ".png", "jpeg": ".jpg"}


def sanitize_filename(raw_name: str | None) -> str:
    """
    Returns a safe display name: no folders, no unusual characters, limited length.
    The original name is kept only for display. Storage uses generated names.
    """
    base_name = os.path.basename(raw_name or "")
    cleaned = re.sub(r"[^A-Za-z0-9._ -]", "_", base_name).strip(" .")
    if not cleaned:
        return "document"
    return cleaned[:MAX_FILENAME_LENGTH]


def detect_file_type(content: bytes) -> str | None:
    """
    Returns "pdf", "png", "jpeg", or "webp" based on the file's first bytes, or None.
    WebP is detected by "RIFF" at the start and "WEBP" at byte 8, because
    other RIFF formats such as WAV also start with "RIFF".
    """
    for file_type, signature in FILE_SIGNATURES.items():
        if content.startswith(signature):
            return file_type
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    return None


def convert_webp_to_png(content: bytes) -> bytes:
    """
    Decodes WebP bytes with OpenCV and re-encodes them as PNG bytes.
    Raises ValueError if the image is damaged and cannot be decoded.
    """
    image = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to decode the WebP image.")

    success, encoded = cv2.imencode(".png", image)
    if not success:
        raise ValueError("Unable to encode the image as PNG.")
    return encoded.tobytes()


def run_ocr(file_path: str, file_type: str) -> str:
    """Runs OCR on a PDF or an image and returns the extracted text."""
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    return extract_text_from_image_path(file_path)


def build_chunks_with_embeddings(ocr_text: str) -> list[tuple[str, list[float]]]:
    """
    Splits the OCR text into chunks and embeds each one for chat search.
    Runs before any database write, so a failure saves nothing.
    """
    if not ocr_text or not ocr_text.strip():
        return []

    chunks = chunk_text(ocr_text)
    if not chunks:
        return []

    embeddings = embed_texts(chunks)
    return list(zip(chunks, embeddings))


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Uploads a document, converts WebP to PNG if needed, reads its text with OCR,
    and classifies it. Only blood test reports create health records. Every
    document is stored and can be searched in chat.
    """
    safe_name = sanitize_filename(file.filename)
    _, extension = os.path.splitext(safe_name)
    extension = extension.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Accepted types: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    file_content = await file.read()
    if len(file_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )
    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB.",
        )

    file_type = detect_file_type(file_content)
    if file_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The file is not a valid JPG, PNG, WebP, or PDF.",
        )

    # WebP is converted to PNG so the rest of the pipeline handles one image format
    if file_type == "webp":
        try:
            file_content = convert_webp_to_png(file_content)
        except ValueError:
            logger.exception("WebP conversion failed for user %s", current_user.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The WebP image could not be read. Please try a different file.",
            )
        file_type = "png"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=TEMP_SUFFIX[file_type]) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        extracted_text = await run_in_threadpool(run_ocr, tmp_path, file_type)
        file_url = await run_in_threadpool(upload_file_to_cloudinary, tmp_path)
    except Exception:
        logger.exception("Document processing failed for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to process the uploaded document. Please try a different file.",
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    parsed = parse_blood_report(extracted_text)

    try:
        chunks_with_embeddings = await run_in_threadpool(build_chunks_with_embeddings, extracted_text)
    except Exception:
        logger.exception("Embedding failed for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to index the document for chat. Please try again.",
        )

    try:
        new_document = Document(
            user_id=current_user.id,
            original_filename=safe_name,
            file_url=file_url,
            file_type="pdf" if file_type == "pdf" else "image",
            ocr_status="completed",
            ocr_text=extracted_text,
            document_type=parsed["document_type"],
            report_date=parsed["report_date"],
            lab_name=parsed["lab_name"],
            panel_name=parsed["panel_name"],
        )
        db.add(new_document)
        db.flush()  # gives new_document an id without committing yet

        if parsed["document_type"] == BLOOD_REPORT_TYPE:
            for row in parsed["rows"]:
                db.add(
                    HealthRecord(
                        user_id=current_user.id,
                        document_id=new_document.id,
                        metric_name=row["metric_name"],
                        panel=row["panel"],
                        value=row["value"],
                        unit=row["unit"],
                        status=row["status"],
                        printed_low=row["printed_low"],
                        printed_high=row["printed_high"],
                        recorded_date=parsed["report_date"],
                    )
                )

        for chunk_text_value, embedding in chunks_with_embeddings:
            db.add(
                DocumentChunk(
                    user_id=current_user.id,
                    document_id=new_document.id,
                    chunk_text=chunk_text_value,
                    embedding=embedding,
                )
            )

        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Saving document failed for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save the document. Please try again.",
        )

    db.refresh(new_document)
    return new_document


@router.get("/", response_model=list[DocumentResponse])
def list_my_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns all documents uploaded by the currently logged-in user."""
    return (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns one document, only if it belongs to the current user."""
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
    """Deletes one document and its health records and chunks, only if the user owns it."""
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

    try:
        db.delete(document)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Deleting document %s failed", document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete the document. Please try again.",
        )