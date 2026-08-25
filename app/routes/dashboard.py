from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import DashboardSummary, TrendPoint
from app.services.analytics import get_dashboard_summary, get_dashboard_trends

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/summary", response_model=DashboardSummary)
def read_dashboard_summary(db: Session = Depends(get_db)):
    return get_dashboard_summary(db)

@router.get("/trends", response_model=List[TrendPoint])
def read_dashboard_trends(db: Session = Depends(get_db)):
    return get_dashboard_trends(db)
