import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_dashboard_summary_api():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_merchants" in data
    assert "total_gmv" in data
    assert data["total_merchants"] > 0

def test_dashboard_trends_api():
    response = client.get("/api/dashboard/trends")
    assert response.status_code == 200
    trends = response.json()
    assert isinstance(trends, list)
    assert len(trends) > 0

def test_merchants_list_api():
    response = client.get("/api/merchants?segment=Healthy")
    assert response.status_code == 200
    merchants = response.json()
    assert isinstance(merchants, list)

def test_merchant_detail_api():
    response = client.get("/api/merchants/MCH0001")
    assert response.status_code == 200
    detail = response.json()
    assert detail["merchant_id"] == "MCH0001"
    assert "health_components" in detail
    assert "decision_explanation" in detail

def test_opportunities_api():
    response = client.get("/api/opportunities")
    assert response.status_code == 200
    opps = response.json()
    assert isinstance(opps, list)

def test_data_quality_api():
    response = client.get("/api/data-quality")
    assert response.status_code == 200
    report = response.json()
    assert report["missing_merchant_ids"] == 0
    assert report["negative_amounts"] == 0
