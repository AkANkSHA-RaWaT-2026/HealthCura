from pydantic import BaseModel
from datetime import datetime


class AdminStats(BaseModel):
    total_patients: int
    total_documents: int
    total_health_records: int
    total_chat_messages: int


class PatientSummary(BaseModel):
    id: int
    full_name: str
    email: str
    document_count: int
    created_at: datetime

    class Config:
        from_attributes = True