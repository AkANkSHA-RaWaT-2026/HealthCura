"""Model for one test result read from a document, such as one hemoglobin value."""

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class HealthRecord(Base):
    """One test result read from a blood report."""

    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)

    metric_name = Column(String, nullable=False, index=True)
    panel = Column(String, nullable=True)  # "Complete Blood Count (CBC)", "Lipid Profile", etc.
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    status = Column(String, nullable=True)  # "low", "high", "normal", "unknown"

    # Reference range printed on the report. Null when no readable range was printed.
    printed_low = Column(Float, nullable=True)
    printed_high = Column(Float, nullable=True)

    recorded_date = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", backref="health_records")