from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import date, datetime

class HealthScoreComponents(BaseModel):
    growth_score: float
    frequency_score: float
    recency_score: float
    value_score: float
    success_rate_score: float
    overall_score: float

class MonthlyPerformance(BaseModel):
    month: str
    transaction_count: int
    gmv: float
    success_rate: float

class MerchantBase(BaseModel):
    merchant_id: str
    merchant_name: str
    merchant_category: str
    city: str
    state: str
    onboarding_date: str

class MerchantSummary(MerchantBase):
    total_transactions: int
    total_transaction_value: float
    avg_transaction_value: float
    success_rate: float
    active_days: int
    last_transaction_date: Optional[str]
    growth_rate: float
    health_score: float
    segment: str
    recommended_action: str

class MerchantDetail(MerchantSummary):
    health_components: HealthScoreComponents
    monthly_history: List[MonthlyPerformance]
    decision_explanation: str

class DashboardSummary(BaseModel):
    total_merchants: int
    active_merchants: int
    total_transactions: int
    total_gmv: float
    overall_success_rate: float
    at_risk_count: int

class TrendPoint(BaseModel):
    month: str
    gmv: float
    volume: int
    active_merchants: int

class SegmentDistribution(BaseModel):
    segment: str
    count: int
    percentage: float
    recommended_action: str

class AcquisitionOpportunity(BaseModel):
    city: str
    category: str
    opportunity_score: float
    demand_gmv: float
    demand_volume: int
    existing_merchant_count: int
    avg_transaction_value: float
    growth_rate: float

class DataQualityReport(BaseModel):
    total_transactions: int
    total_merchants: int
    total_users: int
    missing_merchant_ids: int
    missing_user_ids: int
    negative_amounts: int
    invalid_dates: int
    duplicate_transactions: int
    success_transactions: int
    failed_transactions: int
    pending_transactions: int
