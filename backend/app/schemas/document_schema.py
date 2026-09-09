from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentResponse(BaseModel):
    """Document data returned to the frontend."""
    id: int
    original_filename: str
    file_url: str
    file_type: str
    ocr_status: str
    ocr_text: Optional[str] = None
    ai_summary: Optional[str] = None
    document_type: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True