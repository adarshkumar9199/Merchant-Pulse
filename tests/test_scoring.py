import pytest
from app.services.merchant_scoring import calculate_health_score, classify_merchant_segment

def test_health_score_calculation():
    # Test High Growth, High Volume merchant
    scores = calculate_health_score(
        growth_rate=80.0,
        current_30d_txns=200,
        current_30d_gmv=300000.0,
        last_txn_date="2026-08-14",
        success_rate=98.0
    )

    assert scores["overall_score"] >= 80.0
    assert scores["growth_score"] > 80.0
    assert scores["recency_score"] == 100.0
    assert scores["success_rate_score"] == 98.0

def test_at_risk_segmentation():
    scores = calculate_health_score(
        growth_rate=-40.0,
        current_30d_txns=10,
        current_30d_gmv=5000.0,
        last_txn_date="2026-06-01",  # 75+ days inactive
        success_rate=72.0
    )

    segment, action = classify_merchant_segment(
        health_scores=scores,
        growth_rate=-40.0,
        success_rate=72.0,
        recency_days=75
    )

    assert segment == "At Risk"
    assert action == "Investigate + Intervene"
