"""Response shape for documents returned to the frontend."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """A document with its OCR text, summary, and blood report header fields."""

    id: int
    original_filename: str
    file_url: str
    file_type: str
    ocr_status: str
    ocr_text: Optional[str] = None
    ai_summary: Optional[str] = None
    document_type: Optional[str] = None
    report_date: Optional[date] = None
    lab_name: Optional[str] = None
    panel_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True