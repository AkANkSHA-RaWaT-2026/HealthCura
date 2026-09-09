# backend/app/routers/timeline_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.health_record import HealthRecord
from app.schemas.health_record_schema import HealthRecordResponse

router = APIRouter(prefix="/timeline", tags=["Timeline"])


@router.get("/", response_model=list[HealthRecordResponse])
def get_my_timeline(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns all health metrics extracted from the current user's documents,
    ordered by recorded date (falls back to created_at if no date was found).
    """
    records = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == current_user.id)
        .order_by(HealthRecord.recorded_date.asc().nulls_last(), HealthRecord.created_at.asc())
        .all()
    )
    return records