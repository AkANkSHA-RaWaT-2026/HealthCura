from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.core.database import Base


class DocumentChunk(Base):
    """A piece of a document's OCR text, embedded as a vector for semantic search."""

    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)

    chunk_text = Column(Text, nullable=False)
    # all-MiniLM-L6-v2 produces 384-dimensional embeddings
    embedding = Column(Vector(384), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())