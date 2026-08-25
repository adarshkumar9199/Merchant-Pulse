from typing import Dict, Any, Tuple
from datetime import datetime

# Reference date for static dataset evaluation
DATASET_REF_DATE = datetime(2026, 8, 15)

def calculate_health_score(
    growth_rate: float,
    current_30d_txns: int,
    current_30d_gmv: float,
    last_txn_date: str,
    success_rate: float
) -> Dict[str, float]:
    """
    Calculates explainable 0-100 Merchant Health Score based on 5 weighted components.
    """

    # 1. Growth Score (30%)
    # Normalized: <= -50% growth is 0, >= +100% growth is 100
    if growth_rate is None:
        growth_rate = 0.0
    growth_score = min(100.0, max(0.0, (growth_rate + 50.0) / 1.5))

    # 2. Frequency Score (20%)
    # Target: 150 transactions / 30 days = 100 score
    frequency_score = min(100.0, (current_30d_txns / 150.0) * 100.0)

    # 3. Recency Score (20%)
    # Days since last transaction from dataset reference date
    recency_days = 999
    if last_txn_date:
        try:
            dt = datetime.strptime(str(last_txn_date)[:10], "%Y-%m-%d")
            recency_days = (DATASET_REF_DATE - dt).days
        except Exception:
            recency_days = 999

    if recency_days <= 2:
        recency_score = 100.0
    elif recency_days <= 7:
        recency_score = 85.0
    elif recency_days <= 15:
        recency_score = 70.0
    elif recency_days <= 30:
        recency_score = 45.0
    elif recency_days <= 60:
        recency_score = 20.0
    else:
        recency_score = 0.0

    # 4. Transaction Value Score (15%)
    # Target: 250,000 INR GMV in 30 days = 100 score
    value_score = min(100.0, (current_30d_gmv / 250000.0) * 100.0)

    # 5. Success Rate Score (15%)
    # Directly uses success rate percentage (0 - 100)
    success_rate_score = min(100.0, max(0.0, success_rate))

    # Weighted Overall Score
    overall = (
        (0.30 * growth_score) +
        (0.20 * frequency_score) +
        (0.20 * recency_score) +
        (0.15 * value_score) +
        (0.15 * success_rate_score)
    )

    return {
        "growth_score": round(growth_score, 1),
        "frequency_score": round(frequency_score, 1),
        "recency_score": round(recency_score, 1),
        "value_score": round(value_score, 1),
        "success_rate_score": round(success_rate_score, 1),
        "overall_score": round(overall, 1),
        "recency_days": recency_days
    }

def classify_merchant_segment(
    health_scores: Dict[str, float],
    growth_rate: float,
    success_rate: float,
    recency_days: int
) -> Tuple[str, str]:
    """
    Classifies merchant into a strategic business segment and returns segment tag + recommended action.
    """
    overall = health_scores["overall_score"]
    growth_s = health_scores["growth_score"]

    # 1. At Risk (Red Alert)
    if overall < 40.0 or success_rate < 85.0 or recency_days > 45:
        return "At Risk", "Investigate + Intervene"

    # 2. Declining (Yellow Warning)
    if growth_rate < -15.0 or growth_s <= 35.0:
        return "Declining", "Re-engage"

    # 3. High Growth (Rocket Launch)
    if growth_s >= 70.0 and overall >= 70.0:
        return "High Growth", "Retain + Upsell"

    # 4. Healthy (Green Shield)
    if overall >= 75.0:
        return "Healthy", "Retain"

    # 5. Stable (Default Blue)
    return "Stable", "Monitor"
