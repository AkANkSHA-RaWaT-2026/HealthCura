# backend/app/schemas/health_record_schema.py
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class HealthRecordResponse(BaseModel):
    id: int
    metric_name: str
    value: float
    unit: Optional[str] = None
    status: Optional[str] = None
    recorded_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True