import os
import json
import pandas as pd
import io
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Depends, Query, Form, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db, engine
from app.routes import dashboard, merchants, analytics
from app.services.analytics import (
    get_dashboard_summary, get_dashboard_trends, get_segment_distribution,
    get_acquisition_opportunities, get_merchant_list, get_merchant_detail,
    get_data_quality_report
)
from app.services.charts import (
    render_gmv_trend_svg, render_volume_bar_svg, render_segment_donut_svg,
    render_merchant_history_svg
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "app", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(
    title="Merchant Growth & Retention Decision Engine",
    description="Turning digital payment transaction data into actionable merchant growth decisions.",
    version="1.0.0"
)

# Mount Static Files
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

from fastapi import Response

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

@app.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
def chrome_devtools_probe():
    return Response(status_code=204)

# Jinja2 Template Filters (Pure Python formatting)
def format_currency(val):
    if val is None: return "₹0"
    amt = float(val)
    if amt >= 10000000:
        return f"₹{amt / 10000000:.2f} Cr"
    if amt >= 100000:
        return f"₹{amt / 100000:.2f} L"
    return f"₹{amt:,.0f}"

def format_number(val):
    if val is None: return "0"
    return f"{int(val):,}"

templates.env.filters["currency"] = format_currency
templates.env.filters["number"] = format_number

# Include REST API Routers
app.include_router(dashboard.router)
app.include_router(merchants.router)
app.include_router(analytics.router)

# --------------------------------------------------------------------
# 100% Pure Python Server-Side Rendered (SSR) HTML Routes
# --------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def page_dashboard(
    request: Request,
    search: Optional[str] = Query(None),
    city: Optional[str] = Query("ALL"),
    category: Optional[str] = Query("ALL"),
    segment: Optional[str] = Query("ALL"),
    db: Session = Depends(get_db)
):
    # Calculate all metrics directly in Python before rendering
    summary = get_dashboard_summary(db)
    trends = get_dashboard_trends(db)
    segments = get_segment_distribution(db)
    opportunities = get_acquisition_opportunities(db)
    merchants_list = get_merchant_list(
        db=db,
        search=search,
        city=city if city != "ALL" else None,
        category=category if category != "ALL" else None,
        segment=segment if segment != "ALL" else None,
        limit=50
    )

    # Pure Python SVG Chart Rendering
    svg_gmv_trend = render_gmv_trend_svg(trends)
    svg_volume_bar = render_volume_bar_svg(trends)
    svg_segment_donut = render_segment_donut_svg(segments)

    now_str = datetime.now().strftime("%I:%M:%S %p")

    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "page": "dashboard",
            "summary": summary,
            "svg_gmv_trend": svg_gmv_trend,
            "svg_volume_bar": svg_volume_bar,
            "svg_segment_donut": svg_segment_donut,
            "opportunities": opportunities[:4],
            "merchants": merchants_list,
            "search": search or "",
            "selected_city": city or "ALL",
            "selected_category": category or "ALL",
            "selected_segment": segment or "ALL",
            "last_updated": now_str
        }
    )

@app.get("/merchants", response_class=HTMLResponse)
def page_merchants(
    request: Request,
    search: Optional[str] = Query(None),
    city: Optional[str] = Query("ALL"),
    category: Optional[str] = Query("ALL"),
    segment: Optional[str] = Query("ALL"),
    db: Session = Depends(get_db)
):
    merchants_list = get_merchant_list(
        db=db,
        search=search,
        city=city if city != "ALL" else None,
        category=category if category != "ALL" else None,
        segment=segment if segment != "ALL" else None,
        limit=None
    )
    now_str = datetime.now().strftime("%I:%M:%S %p")

    return templates.TemplateResponse(
        request=request,
        name="merchants.html",
        context={
            "page": "merchants",
            "merchants": merchants_list,
            "search": search or "",
            "selected_city": city or "ALL",
            "selected_category": category or "ALL",
            "selected_segment": segment or "ALL",
            "last_updated": now_str
        }
    )

@app.get("/merchants/{merchant_id}", response_class=HTMLResponse)
def page_merchant_detail(request: Request, merchant_id: str, db: Session = Depends(get_db)):
    detail = get_merchant_detail(db, merchant_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Merchant not found")

    svg_detail_history = render_merchant_history_svg(detail.monthly_history)
    now_str = datetime.now().strftime("%I:%M:%S %p")

    return templates.TemplateResponse(
        request=request, 
        name="merchant_detail.html", 
        context={
            "page": "merchants",
            "merchant_id": merchant_id,
            "merchant": detail,
            "svg_detail_history": svg_detail_history,
            "last_updated": now_str
        }
    )

@app.post("/import-csv-action")
def import_csv_action(
    dataset_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        content = file.file.read()
        df = pd.read_csv(io.BytesIO(content))

        if dataset_type == "merchants":
            required_cols = {'merchant_id', 'merchant_name', 'merchant_category', 'city', 'state', 'onboarding_date'}
            df[list(required_cols)].to_sql("merchants", con=db.bind, if_exists="append", index=False)
        elif dataset_type == "transactions":
            required_cols = {'transaction_id', 'merchant_id', 'user_id', 'transaction_date', 'transaction_amount', 'transaction_status', 'payment_type', 'failure_reason'}
            df[list(required_cols)].to_sql("transactions", con=db.bind, if_exists="append", index=False)

        db.commit()
        from app.services.analytics import clear_analytics_cache
        clear_analytics_cache()
    except Exception as e:
        db.rollback()
    
    return RedirectResponse(url="/", status_code=303)
