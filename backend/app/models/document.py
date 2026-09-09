# backend/app/models/document.py
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
    file_url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)

    ocr_status = Column(String, nullable=False, default="pending")
    ocr_text = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)

    document_type = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", backref="documents")
    health_records = relationship("HealthRecord", cascade="all, delete-orphan")