from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Document(Base):
    """Represents an uploaded medical document (lab report, prescription, etc.)."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    original_filename = Column(String, nullable=False)
    file_url = Column(String, nullable=False)          # Cloudinary URL
    file_type = Column(String, nullable=False)          # "image" or "pdf"

    ocr_status = Column(String, nullable=False, default="pending")  # pending, processing, completed, failed
    ocr_text = Column(Text, nullable=True)               # raw extracted text
    ai_summary = Column(Text, nullable=True)
    
    document_type = Column(String, nullable=True)        # e.g. "lab_report", "prescription" (set later, Feature 3)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", backref="documents")