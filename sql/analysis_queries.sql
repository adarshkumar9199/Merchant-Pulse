-- ====================================================================
-- SQL Analytical Views & Queries - Merchant Decision Engine
-- ====================================================================

-- Drop view if exists
DROP VIEW IF EXISTS vw_merchant_analytics;

-- 1. Comprehensive Merchant Analytics View
-- Calculates 30-day window comparison, success rates, active days, and MoM growth rate
CREATE VIEW vw_merchant_analytics AS
WITH merchant_base AS (
    SELECT 
        m.merchant_id,
        m.merchant_name,
        m.merchant_category,
        m.city,
        m.state,
        m.onboarding_date,
        COUNT(t.transaction_id) AS total_transactions,
        SUM(CASE WHEN t.transaction_status = 'SUCCESS' THEN t.transaction_amount ELSE 0 END) AS total_transaction_value,
        AVG(CASE WHEN t.transaction_status = 'SUCCESS' THEN t.transaction_amount ELSE NULL END) AS avg_transaction_value,
        SUM(CASE WHEN t.transaction_status = 'SUCCESS' THEN 1 ELSE 0 END) AS successful_transactions,
        SUM(CASE WHEN t.transaction_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_transactions,
        ROUND(
            CAST(SUM(CASE WHEN t.transaction_status = 'SUCCESS' THEN 1 ELSE 0 END) AS FLOAT) / 
            NULLIF(COUNT(t.transaction_id), 0) * 100, 2
        ) AS success_rate,
        COUNT(DISTINCT DATE(t.transaction_date)) AS active_days,
        MAX(t.transaction_date) AS last_transaction_date
    FROM merchants m
    LEFT JOIN transactions t ON m.merchant_id = t.merchant_id
    GROUP BY m.merchant_id, m.merchant_name, m.merchant_category, m.city, m.state, m.onboarding_date
),
current_30_days AS (
    -- Current Period (Last 30 Days from max dataset date: 2026-08-15)
    SELECT 
        merchant_id,
        COUNT(transaction_id) AS current_period_transactions,
        SUM(CASE WHEN transaction_status = 'SUCCESS' THEN transaction_amount ELSE 0 END) AS current_period_gmv
    FROM transactions
    WHERE transaction_date >= '2026-07-16 00:00:00'
    GROUP BY merchant_id
),
previous_30_days AS (
    -- Previous Period (Days 31 to 60 prior: 2026-06-16 to 2026-07-15)
    SELECT 
        merchant_id,
        COUNT(transaction_id) AS previous_period_transactions,
        SUM(CASE WHEN transaction_status = 'SUCCESS' THEN transaction_amount ELSE 0 END) AS previous_period_gmv
    FROM transactions
    WHERE transaction_date >= '2026-06-16 00:00:00' 
      AND transaction_date < '2026-07-16 00:00:00'
    GROUP BY merchant_id
)
SELECT 
    b.merchant_id,
    b.merchant_name,
    b.merchant_category,
    b.city,
    b.state,
    b.onboarding_date,
    b.total_transactions,
    COALESCE(b.total_transaction_value, 0) AS total_transaction_value,
    COALESCE(ROUND(b.avg_transaction_value, 2), 0) AS avg_transaction_value,
    b.successful_transactions,
    b.failed_transactions,
    COALESCE(b.success_rate, 0) AS success_rate,
    b.active_days,
    b.last_transaction_date,
    COALESCE(p.previous_period_transactions, 0) AS previous_period_transactions,
    COALESCE(c.current_period_transactions, 0) AS current_period_transactions,
    COALESCE(p.previous_period_gmv, 0) AS previous_period_gmv,
    COALESCE(c.current_period_gmv, 0) AS current_period_gmv,
    ROUND(
        CASE 
            WHEN COALESCE(p.previous_period_transactions, 0) = 0 THEN 
                CASE WHEN COALESCE(c.current_period_transactions, 0) > 0 THEN 100.0 ELSE 0.0 END
            ELSE 
                ((CAST(c.current_period_transactions AS FLOAT) - p.previous_period_transactions) / p.previous_period_transactions) * 100.0
        END, 2
    ) AS growth_rate
FROM merchant_base b
LEFT JOIN current_30_days c ON b.merchant_id = c.merchant_id
LEFT JOIN previous_30_days p ON b.merchant_id = p.merchant_id;


-- 2. Standalone Portfolio Query A: Monthly MoM Growth per Merchant using Window Functions (LAG)
-- Query demonstrating LAG(), SUM() OVER(), and CTEs
/*
WITH monthly_merchant_gmv AS (
    SELECT 
        merchant_id,
        STRFTIME('%Y-%m', transaction_date) AS gmv_month,
        COUNT(transaction_id) AS monthly_txns,
        SUM(CASE WHEN transaction_status = 'SUCCESS' THEN transaction_amount ELSE 0 END) AS monthly_gmv
    FROM transactions
    GROUP BY merchant_id, gmv_month
),
monthly_lag AS (
    SELECT 
        merchant_id,
        gmv_month,
        monthly_txns,
        monthly_gmv,
        LAG(monthly_gmv, 1) OVER (PARTITION BY merchant_id ORDER BY gmv_month) AS prev_month_gmv
    FROM monthly_merchant_gmv
)
SELECT 
    merchant_id,
    gmv_month,
    monthly_gmv,
    prev_month_gmv,
    ROUND(((monthly_gmv - prev_month_gmv) / NULLIF(prev_month_gmv, 0)) * 100, 2) AS mom_growth_pct
FROM monthly_lag
ORDER BY merchant_id, gmv_month;
*/

-- 3. Standalone Portfolio Query B: City & Category Acquisition Opportunity Matrix
-- Identifies areas with high transaction volume but low merchant count
/*
WITH category_city_demand AS (
    SELECT 
        m.city,
        m.merchant_category,
        COUNT(DISTINCT m.merchant_id) AS existing_merchant_count,
        COUNT(t.transaction_id) AS total_demand_volume,
        SUM(CASE WHEN t.transaction_status = 'SUCCESS' THEN t.transaction_amount ELSE 0 END) AS total_demand_gmv,
        AVG(CASE WHEN t.transaction_status = 'SUCCESS' THEN t.transaction_amount ELSE NULL END) AS avg_ticket_size
    FROM merchants m
    LEFT JOIN transactions t ON m.merchant_id = t.merchant_id
    GROUP BY m.city, m.merchant_category
    HAVING COUNT(DISTINCT m.merchant_id) > 0
)
SELECT 
    city,
    merchant_category,
    existing_merchant_count,
    total_demand_volume,
    total_demand_gmv,
    ROUND(avg_ticket_size, 2) AS avg_ticket_size,
    DENSE_RANK() OVER (ORDER BY total_demand_gmv DESC) AS gmv_rank,
    DENSE_RANK() OVER (ORDER BY (total_demand_gmv / existing_merchant_count) DESC) AS opportunity_rank
FROM category_city_demand
ORDER BY opportunity_rank ASC;
*/
