from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import SegmentDistribution, AcquisitionOpportunity, DataQualityReport
from app.services.analytics import (
    get_segment_distribution, get_acquisition_opportunities, get_data_quality_report
)

router = APIRouter(prefix="/api", tags=["analytics"])

@router.get("/segments", response_model=List[SegmentDistribution])
def read_segment_distribution(db: Session = Depends(get_db)):
    return get_segment_distribution(db)

@router.get("/opportunities", response_model=List[AcquisitionOpportunity])
def read_acquisition_opportunities(db: Session = Depends(get_db)):
    return get_acquisition_opportunities(db)

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
import pandas as pd
import io

@router.get("/data-quality", response_model=DataQualityReport)
def read_data_quality(db: Session = Depends(get_db)):
    return get_data_quality_report(db)

@router.post("/import-csv")
async def import_csv_data(
    dataset_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(('.csv', '.CSV', '.txt')):
        raise HTTPException(status_code=400, detail="Only CSV or TXT data files are supported.")

    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))

        if dataset_type == "merchants":
            required_cols = {'merchant_id', 'merchant_name', 'merchant_category', 'city', 'state', 'onboarding_date'}
            if not required_cols.issubset(set(df.columns)):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid columns for merchants CSV. Missing required: {list(required_cols - set(df.columns))}"
                )
            
            # Append merchants to database
            df[list(required_cols)].to_sql("merchants", con=db.bind, if_exists="append", index=False)
            db.commit()
            return {"message": f"Successfully imported {len(df)} new merchants into database!", "count": len(df)}

        elif dataset_type == "transactions":
            required_cols = {'transaction_id', 'merchant_id', 'user_id', 'transaction_date', 'transaction_amount', 'transaction_status', 'payment_type', 'failure_reason'}
            if not required_cols.issubset(set(df.columns)):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid columns for transactions CSV. Missing required: {list(required_cols - set(df.columns))}"
                )

            # Append transactions to database
            df[list(required_cols)].to_sql("transactions", con=db.bind, if_exists="append", index=False)
            db.commit()
            return {"message": f"Successfully imported {len(df)} transactions into database!", "count": len(df)}

        else:
            raise HTTPException(status_code=400, detail="Unsupported dataset type. Choose 'merchants' or 'transactions'.")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to import file: {str(e)}")

