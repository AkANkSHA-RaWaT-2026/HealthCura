"""Response shape for one health record, including its printed reference range."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class HealthRecordResponse(BaseModel):
    """One test result with its panel, status, and printed range when available."""

    id: int
    metric_name: str
    panel: Optional[str] = None
    value: float
    unit: Optional[str] = None
    status: Optional[str] = None
    printed_low: Optional[float] = None
    printed_high: Optional[float] = None
    recorded_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True