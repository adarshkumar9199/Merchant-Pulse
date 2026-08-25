import time
import pandas as pd
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.merchant_scoring import calculate_health_score, classify_merchant_segment
from app.services.recommendations import generate_recommendation_and_explanation
from app.schemas import (
    DashboardSummary, TrendPoint, MerchantSummary, MerchantDetail, 
    HealthScoreComponents, MonthlyPerformance, SegmentDistribution, 
    AcquisitionOpportunity, DataQualityReport
)

DATASET_REF_DATE_STR = "2026-08-15"

# In-Memory Cache Containers & Timestamps
_MERCHANT_LIST_CACHE = None
_SUMMARY_CACHE = None
_TRENDS_CACHE = None
_SEGMENT_CACHE = None
_OPPORTUNITY_CACHE = None
_CACHE_TIMESTAMP = 0
CACHE_TTL_SECONDS = 300  # 5 Minutes

def clear_analytics_cache():
    global _MERCHANT_LIST_CACHE, _SUMMARY_CACHE, _TRENDS_CACHE, _SEGMENT_CACHE, _OPPORTUNITY_CACHE, _CACHE_TIMESTAMP
    _MERCHANT_LIST_CACHE = None
    _SUMMARY_CACHE = None
    _TRENDS_CACHE = None
    _SEGMENT_CACHE = None
    _OPPORTUNITY_CACHE = None
    _CACHE_TIMESTAMP = 0

def get_merchant_list_raw(db: Session) -> List[Dict[str, Any]]:
    global _MERCHANT_LIST_CACHE, _CACHE_TIMESTAMP
    now = time.time()

    if _MERCHANT_LIST_CACHE is not None and (now - _CACHE_TIMESTAMP) < CACHE_TTL_SECONDS:
        return _MERCHANT_LIST_CACHE

    query = text("SELECT * FROM vw_merchant_analytics;")
    rows = db.execute(query).mappings().fetchall()

    merchants_processed = []
    for r in rows:
        m_dict = dict(r)
        
        scores = calculate_health_score(
            growth_rate=m_dict.get("growth_rate") or 0.0,
            current_30d_txns=m_dict.get("current_period_transactions") or 0,
            current_30d_gmv=m_dict.get("current_period_gmv") or 0.0,
            last_txn_date=m_dict.get("last_transaction_date"),
            success_rate=m_dict.get("success_rate") or 0.0
        )

        segment, rec_action = classify_merchant_segment(
            health_scores=scores,
            growth_rate=m_dict.get("growth_rate") or 0.0,
            success_rate=m_dict.get("success_rate") or 0.0,
            recency_days=scores["recency_days"]
        )

        m_dict["health_score"] = scores["overall_score"]
        m_dict["health_components"] = scores
        m_dict["segment"] = segment
        m_dict["recommended_action"] = rec_action
        merchants_processed.append(m_dict)

    _MERCHANT_LIST_CACHE = merchants_processed
    _CACHE_TIMESTAMP = now
    return merchants_processed

def get_dashboard_summary(db: Session) -> DashboardSummary:
    global _SUMMARY_CACHE, _CACHE_TIMESTAMP
    now = time.time()

    if _SUMMARY_CACHE is not None and (now - _CACHE_TIMESTAMP) < CACHE_TTL_SECONDS:
        return _SUMMARY_CACHE

    query = text("""
        SELECT 
            COUNT(DISTINCT m.merchant_id) as total_merchants,
            COUNT(DISTINCT CASE WHEN t.transaction_date >= '2026-07-16' THEN t.merchant_id END) as active_merchants,
            COUNT(t.transaction_id) as total_transactions,
            COALESCE(SUM(CASE WHEN t.transaction_status = 'SUCCESS' THEN t.transaction_amount ELSE 0 END), 0) as total_gmv,
            ROUND(
                CAST(SUM(CASE WHEN t.transaction_status = 'SUCCESS' THEN 1 ELSE 0 END) AS FLOAT) / 
                NULLIF(COUNT(t.transaction_id), 0) * 100, 2
            ) as overall_success_rate
        FROM merchants m
        LEFT JOIN transactions t ON m.merchant_id = t.merchant_id;
    """)
    res = db.execute(query).fetchone()

    merchants = get_merchant_list_raw(db)
    at_risk_count = sum(1 for m in merchants if m["segment"] == "At Risk")

    summary = DashboardSummary(
        total_merchants=res.total_merchants or 0,
        active_merchants=res.active_merchants or 0,
        total_transactions=res.total_transactions or 0,
        total_gmv=round(res.total_gmv or 0.0, 2),
        overall_success_rate=res.overall_success_rate or 0.0,
        at_risk_count=at_risk_count
    )

    _SUMMARY_CACHE = summary
    return summary

def get_dashboard_trends(db: Session) -> List[TrendPoint]:
    global _TRENDS_CACHE, _CACHE_TIMESTAMP
    now = time.time()

    if _TRENDS_CACHE is not None and (now - _CACHE_TIMESTAMP) < CACHE_TTL_SECONDS:
        return _TRENDS_CACHE

    query = text("""
        SELECT 
            STRFTIME('%Y-%m', transaction_date) as month,
            COALESCE(SUM(CASE WHEN transaction_status = 'SUCCESS' THEN transaction_amount ELSE 0 END), 0) as gmv,
            COUNT(transaction_id) as volume,
            COUNT(DISTINCT merchant_id) as active_merchants
        FROM transactions
        GROUP BY month
        ORDER BY month ASC;
    """)
    rows = db.execute(query).fetchall()
    trends = [
        TrendPoint(
            month=r.month,
            gmv=round(r.gmv, 2),
            volume=r.volume,
            active_merchants=r.active_merchants
        ) for r in rows if r.month
    ]

    _TRENDS_CACHE = trends
    return trends

def get_segment_distribution(db: Session) -> List[SegmentDistribution]:
    global _SEGMENT_CACHE, _CACHE_TIMESTAMP
    now = time.time()

    if _SEGMENT_CACHE is not None and (now - _CACHE_TIMESTAMP) < CACHE_TTL_SECONDS:
        return _SEGMENT_CACHE

    merchants = get_merchant_list_raw(db)
    total = len(merchants)
    if total == 0:
        return []

    counts: Dict[str, int] = {
        "High Growth": 0,
        "Healthy": 0,
        "Stable": 0,
        "Declining": 0,
        "At Risk": 0
    }
    rec_actions = {
        "High Growth": "Retain + Upsell",
        "Healthy": "Retain",
        "Stable": "Monitor",
        "Declining": "Re-engage",
        "At Risk": "Investigate + Intervene"
    }

    for m in merchants:
        counts[m["segment"]] = counts.get(m["segment"], 0) + 1

    segments = [
        SegmentDistribution(
            segment=seg,
            count=count,
            percentage=round((count / total) * 100, 1),
            recommended_action=rec_actions[seg]
        ) for seg, count in counts.items()
    ]

    _SEGMENT_CACHE = segments
    return segments

def get_acquisition_opportunities(db: Session) -> List[AcquisitionOpportunity]:
    global _OPPORTUNITY_CACHE, _CACHE_TIMESTAMP
    now = time.time()

    if _OPPORTUNITY_CACHE is not None and (now - _CACHE_TIMESTAMP) < CACHE_TTL_SECONDS:
        return _OPPORTUNITY_CACHE

    query = text("""
        WITH city_cat_summary AS (
            SELECT 
                m.city,
                m.merchant_category as category,
                COUNT(DISTINCT m.merchant_id) as merchant_count,
                COUNT(t.transaction_id) as demand_volume,
                SUM(CASE WHEN t.transaction_status = 'SUCCESS' THEN t.transaction_amount ELSE 0 END) as demand_gmv,
                AVG(CASE WHEN t.transaction_status = 'SUCCESS' THEN t.transaction_amount ELSE NULL END) as avg_ticket
            FROM merchants m
            LEFT JOIN transactions t ON m.merchant_id = t.merchant_id
            GROUP BY m.city, m.merchant_category
        ),
        recent_cat_growth AS (
            SELECT 
                m.city,
                m.merchant_category as category,
                SUM(CASE WHEN t.transaction_date >= '2026-07-16' AND t.transaction_status = 'SUCCESS' THEN t.transaction_amount ELSE 0 END) as recent_gmv,
                SUM(CASE WHEN t.transaction_date >= '2026-06-16' AND t.transaction_date < '2026-07-16' AND t.transaction_status = 'SUCCESS' THEN t.transaction_amount ELSE 0 END) as prev_gmv
            FROM merchants m
            LEFT JOIN transactions t ON m.merchant_id = t.merchant_id
            GROUP BY m.city, m.merchant_category
        )
        SELECT 
            c.city,
            c.category,
            c.merchant_count,
            c.demand_volume,
            c.demand_gmv,
            c.avg_ticket,
            g.recent_gmv,
            g.prev_gmv
        FROM city_cat_summary c
        JOIN recent_cat_growth g ON c.city = g.city AND c.category = g.category
        WHERE c.merchant_count > 0;
    """)
    rows = db.execute(query).fetchall()

    if not rows:
        return []

    df = pd.DataFrame([dict(r._mapping) for r in rows])
    
    df["growth_rate"] = df.apply(
        lambda r: ((r["recent_gmv"] - r["prev_gmv"]) / r["prev_gmv"] * 100.0) if r["prev_gmv"] > 0 else 0.0, axis=1
    )

    max_gmv = df["demand_gmv"].max() or 1.0
    max_growth = max(1.0, df["growth_rate"].max())
    max_ticket = df["avg_ticket"].max() or 1.0

    df["demand_score"] = (df["demand_gmv"] / max_gmv) * 100.0
    df["growth_score"] = df["growth_rate"].apply(lambda g: min(100.0, max(0.0, (g + 50.0) / 1.5)))
    df["density_score"] = (1.0 / df["merchant_count"]) * 100.0
    df["density_score"] = (df["density_score"] / df["density_score"].max()) * 100.0
    df["ticket_score"] = (df["avg_ticket"] / max_ticket) * 100.0

    df["opportunity_score"] = (
        (0.35 * df["demand_score"]) +
        (0.25 * df["growth_score"]) +
        (0.25 * df["density_score"]) +
        (0.15 * df["ticket_score"])
    ).round(1)

    df_sorted = df.sort_values(by="opportunity_score", ascending=False)

    opportunities = []
    for _, row in df_sorted.iterrows():
        opportunities.append(AcquisitionOpportunity(
            city=row["city"],
            category=row["category"],
            existing_merchant_count=int(row["merchant_count"]),
            demand_volume=int(row["demand_volume"]),
            demand_gmv=round(float(row["demand_gmv"]), 2),
            avg_transaction_value=round(float(row["avg_ticket"]), 2),
            growth_rate=round(float(row["growth_rate"]), 2),
            opportunity_score=float(row["opportunity_score"])
        ))

    _OPPORTUNITY_CACHE = opportunities
    return opportunities

def get_merchant_list(
    db: Session,
    search: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    segment: Optional[str] = None,
    min_health: Optional[float] = None,
    max_health: Optional[float] = None,
    limit: Optional[int] = None
) -> List[MerchantSummary]:
    
    raw_merchants = get_merchant_list_raw(db)
    filtered = []

    for m in raw_merchants:
        if search:
            s = search.lower()
            m_id = str(m.get("merchant_id", "")).lower()
            m_name = str(m.get("merchant_name", "")).lower()
            m_city = str(m.get("city", "")).lower()
            m_cat = str(m.get("merchant_category", "")).lower()
            if not (s in m_id or s in m_name or s in m_city or s in m_cat):
                continue

        if city and city != "ALL" and m.get("city") != city:
            continue
        if category and category != "ALL" and m.get("merchant_category") != category:
            continue
        if segment and segment != "ALL" and m.get("segment") != segment:
            continue
        if min_health is not None and m["health_score"] < min_health:
            continue
        if max_health is not None and m["health_score"] > max_health:
            continue

        filtered.append(MerchantSummary(
            merchant_id=m["merchant_id"],
            merchant_name=m["merchant_name"],
            merchant_category=m["merchant_category"],
            city=m["city"],
            state=m["state"],
            onboarding_date=str(m["onboarding_date"]),
            total_transactions=m["total_transactions"] or 0,
            total_transaction_value=round(m["total_transaction_value"] or 0.0, 2),
            avg_transaction_value=round(m["avg_transaction_value"] or 0.0, 2),
            success_rate=m["success_rate"] or 0.0,
            active_days=m["active_days"] or 0,
            last_transaction_date=str(m["last_transaction_date"]) if m.get("last_transaction_date") else None,
            growth_rate=m["growth_rate"] or 0.0,
            health_score=m["health_score"],
            segment=m["segment"],
            recommended_action=m["recommended_action"]
        ))

    if limit is not None and limit > 0:
        filtered = filtered[:limit]

    return filtered

def get_merchant_detail(db: Session, merchant_id: str) -> Optional[MerchantDetail]:
    raw_list = get_merchant_list_raw(db)
    target = next((m for m in raw_list if m["merchant_id"] == merchant_id), None)
    if not target:
        return None

    scores = target["health_components"]

    hist_query = text("""
        SELECT 
            STRFTIME('%Y-%m', transaction_date) as month,
            COUNT(transaction_id) as transaction_count,
            COALESCE(SUM(CASE WHEN transaction_status = 'SUCCESS' THEN transaction_amount ELSE 0 END), 0) as gmv,
            ROUND(
                CAST(SUM(CASE WHEN transaction_status = 'SUCCESS' THEN 1 ELSE 0 END) AS FLOAT) / 
                NULLIF(COUNT(transaction_id), 0) * 100, 2
            ) as success_rate
        FROM transactions
        WHERE merchant_id = :m_id
        GROUP BY month
        ORDER BY month ASC;
    """)
    hist_rows = db.execute(hist_query, {"m_id": merchant_id}).fetchall()
    monthly_history = [
        MonthlyPerformance(
            month=r.month,
            transaction_count=r.transaction_count,
            gmv=round(r.gmv, 2),
            success_rate=r.success_rate or 0.0
        ) for r in hist_rows if r.month
    ]

    rec_expl = generate_recommendation_and_explanation(
        merchant_name=target["merchant_name"],
        category=target["merchant_category"],
        segment=target["segment"],
        recommended_action=target["recommended_action"],
        growth_rate=target.get("growth_rate") or 0.0,
        current_30d_txns=target.get("current_period_transactions") or 0,
        previous_30d_txns=target.get("previous_period_transactions") or 0,
        current_30d_gmv=target.get("current_period_gmv") or 0.0,
        success_rate=target.get("success_rate") or 0.0,
        recency_days=scores["recency_days"],
        health_scores=scores
    )

    return MerchantDetail(
        merchant_id=target["merchant_id"],
        merchant_name=target["merchant_name"],
        merchant_category=target["merchant_category"],
        city=target["city"],
        state=target["state"],
        onboarding_date=str(target["onboarding_date"]),
        total_transactions=target["total_transactions"] or 0,
        total_transaction_value=round(target["total_transaction_value"] or 0.0, 2),
        avg_transaction_value=round(target["avg_transaction_value"] or 0.0, 2),
        success_rate=target["success_rate"] or 0.0,
        active_days=target["active_days"] or 0,
        last_transaction_date=str(target["last_transaction_date"]) if target.get("last_transaction_date") else None,
        growth_rate=target["growth_rate"] or 0.0,
        health_score=target["health_score"],
        segment=target["segment"],
        recommended_action=target["recommended_action"],
        health_components=HealthScoreComponents(
            growth_score=scores["growth_score"],
            frequency_score=scores["frequency_score"],
            recency_score=scores["recency_score"],
            value_score=scores["value_score"],
            success_rate_score=scores["success_rate_score"],
            overall_score=scores["overall_score"]
        ),
        monthly_history=monthly_history,
        decision_explanation=rec_expl["decision_explanation"]
    )

def get_data_quality_report(db: Session) -> DataQualityReport:
    total_merchants = db.execute(text("SELECT COUNT(*) FROM merchants;")).scalar() or 0
    total_users = db.execute(text("SELECT COUNT(*) FROM users;")).scalar() or 0
    
    txn_stats = db.execute(text("""
        SELECT 
            COUNT(*) AS total_txns,
            SUM(CASE WHEN merchant_id IS NULL OR merchant_id = '' THEN 1 ELSE 0 END) AS missing_merchant_ids,
            SUM(CASE WHEN user_id IS NULL OR user_id = '' THEN 1 ELSE 0 END) AS missing_user_ids,
            SUM(CASE WHEN transaction_amount < 0 THEN 1 ELSE 0 END) AS negative_amounts,
            SUM(CASE WHEN transaction_date IS NULL OR transaction_date = '' THEN 1 ELSE 0 END) AS invalid_dates,
            SUM(CASE WHEN transaction_status = 'SUCCESS' THEN 1 ELSE 0 END) AS success_txns,
            SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_txns,
            SUM(CASE WHEN transaction_status = 'PENDING' THEN 1 ELSE 0 END) AS pending_txns
        FROM transactions;
    """)).mappings().first()

    dup_count = db.execute(text("""
        SELECT COUNT(transaction_id) - COUNT(DISTINCT transaction_id) FROM transactions;
    """)).scalar() or 0

    return DataQualityReport(
        total_transactions=txn_stats["total_txns"] or 0,
        total_merchants=total_merchants,
        total_users=total_users,
        missing_merchant_ids=txn_stats["missing_merchant_ids"] or 0,
        missing_user_ids=txn_stats["missing_user_ids"] or 0,
        negative_amounts=txn_stats["negative_amounts"] or 0,
        invalid_dates=txn_stats["invalid_dates"] or 0,
        duplicate_transactions=dup_count,
        success_transactions=txn_stats["success_txns"] or 0,
        failed_transactions=txn_stats["failed_txns"] or 0,
        pending_transactions=txn_stats["pending_txns"] or 0
    )
