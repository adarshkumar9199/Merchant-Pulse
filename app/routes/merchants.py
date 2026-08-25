from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas import MerchantSummary, MerchantDetail
from app.services.analytics import get_merchant_list, get_merchant_detail

router = APIRouter(prefix="/api/merchants", tags=["merchants"])

@router.get("", response_model=List[MerchantSummary])
def read_merchants(
    search: Optional[str] = Query(None, description="Search by ID, name, city, category"),
    city: Optional[str] = Query(None, description="Filter by city"),
    category: Optional[str] = Query(None, description="Filter by category"),
    segment: Optional[str] = Query(None, description="Filter by segment"),
    min_health: Optional[float] = Query(None, description="Minimum health score"),
    max_health: Optional[float] = Query(None, description="Maximum health score"),
    limit: Optional[int] = Query(None, description="Limit number of returned merchants"),
    db: Session = Depends(get_db)
):
    return get_merchant_list(
        db=db,
        search=search,
        city=city,
        category=category,
        segment=segment,
        min_health=min_health,
        max_health=max_health,
        limit=limit
    )

@router.get("/{merchant_id}", response_model=MerchantDetail)
def read_merchant_detail(merchant_id: str, db: Session = Depends(get_db)):
    detail = get_merchant_detail(db, merchant_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return detail

@router.post("", status_code=201)
def create_merchant(
    merchant_id: str,
    merchant_name: str,
    merchant_category: str,
    city: str,
    state: str,
    onboarding_date: str,
    db: Session = Depends(get_db)
):
    from app.models import Merchant
    from datetime import datetime

    existing = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Merchant ID already exists")

    try:
        onboard_dt = datetime.strptime(onboarding_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid onboarding_date format. Use YYYY-MM-DD")

    new_m = Merchant(
        merchant_id=merchant_id,
        merchant_name=merchant_name,
        merchant_category=merchant_category,
        city=city,
        state=state,
        onboarding_date=onboard_dt
    )
    db.add(new_m)
    db.commit()
    return {"message": "Merchant created successfully", "merchant_id": merchant_id}

