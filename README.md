# Merchant Growth & Retention Decision Engine

> **Turning digital payment transaction data into actionable merchant decisions.**

---

## 📌 Disclaimer
*This project uses realistic synthetic/simulated digital-payment transaction data for demonstration purposes and does not use proprietary internal data from PhonePe or any other payment platform.*

---

## 🚀 Executive Summary

The **Merchant Growth & Retention Decision Engine** is a production-style, portfolio-ready fintech analytics application. Inspired by decision-support systems inside leading digital payment platforms, it transforms raw transaction processing logs into merchant-level metrics, transparent 0–100 health scores, behavioral segmentations, acquisition opportunity matrix rankings, and programmatic business recommendations.

### Key Business Questions Answered:
1. **Which merchants are growing rapidly?** (High Growth segment target for Soundbox/Credit upsell)
2. **Which merchants are stable and healthy?** (Healthy & Stable segments for standard retention)
3. **Which merchants are declining or at risk?** (Declining & At Risk segments requiring immediate intervention or re-engagement promos)
4. **Where are the merchant acquisition opportunities?** (City + Merchant Category hotspots based on demand vs existing merchant density)
5. **What specific business action should be taken next for each merchant?** (Automated dynamic decision explanation generation)

---

## 🛠️ Architecture & Tech Stack

```
Merchant Growth & Retention Decision Engine/
├── app/
│   ├── main.py                     # FastAPI application & HTML page routes
│   ├── database.py                 # SQLAlchemy engine & session configuration
│   ├── models.py                   # SQLAlchemy ORM models (Merchant, User, Transaction)
│   ├── schemas.py                  # Pydantic validation schemas
│   ├── routes/
│   │   ├── dashboard.py            # API routes for dashboard summary & trends
│   │   ├── merchants.py            # API routes for merchant list & profiles
│   │   └── analytics.py            # API routes for segments, opportunities & data hygiene
│   └── services/
│       ├── merchant_scoring.py     # Transparent 5-Factor Health Score & Segment rules
│       ├── analytics.py            # SQL aggregations, window metrics, opportunity matrix
│       ├── recommendations.py      # Dynamic decision & explanation generator
│       └── data_quality.py        # Automated data quality & validation checks
├── app/templates/
│   ├── index.html                  # Main Fintech Decision Dashboard
│   ├── merchants.html              # Merchant Directory
│   └── merchant_detail.html        # Merchant Profile & 5-Factor Health Gauge
├── static/
│   ├── css/
│   │   └── style.css               # Stripe/Mercury-inspired dark/light design system
│   └── js/
│       ├── dashboard.js            # Dashboard controller & Chart.js graphs
│       ├── merchants.js            # Merchant directory datatable & filter controller
│       └── merchant_detail.js      # Merchant profile timeline chart & gauge logic
├── data/
│   ├── merchants.csv               # Generated 500 merchants
│   ├── users.csv                   # Generated 5,000 users
│   └── transactions.csv            # Generated ~477,000 transactions (12 months)
├── sql/
│   ├── schema.sql                  # DDL table creation & indexes
│   └── analysis_queries.sql        # Portfolio SQL queries (CTEs, LAG, RANK, Window functions)
├── scripts/
│   ├── generate_data.py            # Synthetic dataset generator with behavioral cohorts
│   └── seed_db.py                  # Database initialization & CSV loader
├── tests/
│   ├── test_scoring.py             # Unit tests for scoring & segmentation logic
│   └── test_api.py                 # Integration tests for FastAPI endpoints
├── requirements.txt
└── README.md
```

### Core Technologies:
- **Backend**: Python 3.12, FastAPI, Pandas, NumPy, SQLAlchemy
- **Database**: SQLite (100MB+ dataset, indexed on `merchant_id`, `transaction_date`, `transaction_status`)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (ES6+), Chart.js
- **Testing**: Pytest & HTTPX

---

## 📊 SQL Analytics & Window Functions

The core analytics layer relies on database aggregation rather than loading raw rows into memory. 

### Analytical View (`vw_merchant_analytics`):
Combines 30-day current period vs previous 30-day period transaction metrics using SQL window techniques:
- `SUM(CASE WHEN status='SUCCESS' THEN amount ELSE 0 END)` conditional aggregation.
- `LAG()` and `ROW_NUMBER()` over partition windows to compute Month-over-Month (MoM) growth rates.
- Payment SLA success rates: $\text{Success Rate} = \frac{\text{Successful Txns}}{\text{Total Txns}} \times 100$.

---

## ⚖️ Merchant Health Scoring Methodology (0–100)

Rather than arbitrary black-box machine learning, the engine uses an **explainable 5-component scoring formula**:

$$\text{Health Score} = 0.30 \times \text{Growth} + 0.20 \times \text{Frequency} + 0.20 \times \text{Recency} + 0.15 \times \text{Value} + 0.15 \times \text{Success Rate}$$

| Component | Weight | Calculation Description |
| :--- | :---: | :--- |
| **Growth Score** | 30% | Normalized MoM GMV/Volume % growth rate (clamped 0 to 100) |
| **Frequency Score** | 20% | 30-day transaction volume normalized against 150 txns target |
| **Recency Score** | 20% | Exponential decay based on days since last transaction (0–2 days = 100, 60+ days = 0) |
| **Transaction Value Score** | 15% | 30-day GMV normalized against ₹250,000 target |
| **Success Rate Score** | 15% | Direct payment gateway success rate percentage (0 to 100) |

---

## 🎯 Merchant Behavioral Segmentation

Merchants are categorized based on clear business logic:

| Segment | Icon | Criteria | Recommended Action |
| :--- | :---: | :--- | :--- |
| **High Growth** | 🚀 | Growth Score ≥ 70 AND Health Score ≥ 70 | **Retain + Upsell** (Offer Soundbox & merchant credit line) |
| **Healthy** | 🟢 | Health Score ≥ 75 | **Retain** (Maintain SLA & rebate rewards) |
| **Stable** | 🔵 | Health Score 50 to 74 | **Monitor** (Regular quarterly check-in) |
| **Declining** | 🟡 | MoM Growth Rate < -15% OR Growth Score ≤ 35 | **Re-engage** (Deploy customer checkout cashback promo) |
| **At Risk** | 🔴 | Health Score < 40 OR Success Rate < 85% OR Inactive > 45 days | **Investigate + Intervene** (Field agent visit & gateway inspection) |

---

## 🌐 Acquisition Opportunity Matrix

Identifies underserved city and merchant category expansion targets:

$$\text{Opportunity Score} = 0.35 \times \text{Demand GMV} + 0.25 \times \text{Category Growth} + 0.25 \times \text{Inverse Merchant Density} + 0.15 \times \text{Avg Ticket Size}$$

Example Top Opportunity: **Pune + Grocery** or **Bengaluru + Electronics**.

---

## 💻 How to Run Locally

### 1. Clone & Install Dependencies
```bash
cd "d:/Merchant Growth & Retention Decision Engine"
pip install -r requirements.txt
```

### 2. Generate Synthetic Dataset (Optional - Pre-generated)
```bash
python scripts/generate_data.py
```

### 3. Seed Database & Create Views
```bash
python scripts/seed_db.py
```

### 4. Run Pytest Test Suite
```bash
python -m pytest tests/
```

### 5. Launch FastAPI Application Server
```bash
python -m uvicorn app.main:app --port 5000 --reload
```
Open your browser at **http://127.0.0.1:5000** to view the live dashboard!

> **Note for Windows Users**: Ports 8000 and 8080 are frequently occupied by Windows services. Using `--port 5000` ensures smooth execution without `[WinError 10013]` permission conflicts.

---

## 👨‍💻 Key Interview Talking Points

1. **Why SQLite + SQLAlchemy instead of pulling all rows into Pandas?**
   - Querying 477,000+ raw transactions directly into Python memory for every HTTP request is slow and unscalable. By delegating window aggregations (`vw_merchant_analytics`) to the database SQL engine with index scans on `(merchant_id, transaction_date)`, API response times remain under 25ms.
2. **Why clear rule-based scoring over black-box ML?**
   - In commercial fintech merchant retention, business relationship managers need transparent metrics they can explain to merchants (e.g., "Your volume dropped 40% and failure rate rose to 18%"). Explainability builds trust.
3. **How are recommendations constructed?**
   - The recommendation engine dynamically interpolates metric values into natural language narratives, creating customized executive briefings per merchant.
  
   - ### ✉️ Get in Touch
If you have questions, feedback, or collaboration opportunities:
- **Developer**: Adarsh Kumar
- **Email**: [adarsh.kumar919976@gmail.com](mailto:adarsh.kumar919976@gmail.com)

