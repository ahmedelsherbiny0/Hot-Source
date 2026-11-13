"""
Unit and integration tests for FastAPI REST Endpoints:
- GET /api/v1/health
- GET /api/v1/benchmarks
- POST /api/v1/analyze/variable
- GET /api/v1/scan/benchmarks
"""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.index import app

client = TestClient(app)


def test_health_endpoint():
    """Verify health readiness endpoint returns status, capabilities, and variables."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "capabilities" in data
    assert "supported_variables" in data
    assert "evapotranspiration" in data["supported_variables"]
    assert "chlorophyll_a" in data["supported_variables"]


def test_benchmarks_endpoint():
    """Verify benchmarks endpoint returns the 3 curated NASA case studies."""
    response = client.get("/api/v1/benchmarks")
    assert response.status_code == 200
    benchmarks = response.json()
    assert len(benchmarks) == 3

    ids = {b["id"] for b in benchmarks}
    assert "pearl_river" in ids
    assert "mississippi_west" in ids
    assert "nile_delta" in ids

    for b in benchmarks:
        assert len(b["bbox"]) == 4
        assert "default_variable" in b
        assert "expected_driver" in b


def test_analyze_variable_benchmark_pearl_river():
    """Verify analyze endpoint on Pearl River benchmark case study."""
    payload = {
        "lat": 22.15,
        "lon": 113.7,
        "variable": "chlorophyll_a",
        "start_year": 2003,
        "end_year": 2025,
        "season": "all",
        "region_id": "pearl_river",
    }
    response = client.post("/api/v1/analyze/variable", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["cache_key"] == "benchmark_pearl_river_chlorophyll_a"
    assert data["variable_name"] == "chlorophyll_a"
    assert data["unit"] == "mg/m³"
    assert "series" in data
    assert len(data["series"]) > 0

    # Verify statistical trend metrics
    trend = data["trend"]
    assert "sen_slope" in trend
    assert "cumulative_change" in trend
    assert "p_value" in trend
    assert "test_used" in trend
    assert trend["is_significant"] is True

    # Verify OLS hyperbolic confidence bands
    ols = data["ols"]
    assert len(ols["ci_upper"]) == len(data["series"])
    assert len(ols["ci_lower"]) == len(data["series"])

    # Verify physical driver attribution
    driver = data["physical_driver"]
    assert "driver_name" in driver
    assert "correlation_r" in driver
    assert "driver_reason" in data
    assert len(data["driver_reason"]) > 20


def test_analyze_variable_open_ocean_guardrail():
    """Verify open-ocean coordinates on land-only variables return structured HTTP 422."""
    payload = {
        "lat": 15.0,
        "lon": -150.0,  # Mid-Pacific Ocean
        "variable": "evapotranspiration",
        "start_year": 2005,
        "end_year": 2020,
    }
    response = client.post("/api/v1/analyze/variable", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error_type"] == "spatial_boundary_error"


def test_scan_benchmarks_parallel_and_fdr():
    """Verify multi-region parallel scan computes trends and Benjamini-Hochberg FDR."""
    response = client.get("/api/v1/scan/benchmarks")
    assert response.status_code == 200
    data = response.json()

    assert data["total_regions"] == 3
    assert data["fdr_threshold"] == 0.05
    assert len(data["results"]) == 3

    for item in data["results"]:
        assert "region_id" in item
        assert "sen_slope" in item
        assert "raw_p_value" in item
        assert "fdr_p_value" in item
        assert "is_significant" in item
        assert item["fdr_p_value"] >= item["raw_p_value"] or np.isclose(item["fdr_p_value"], item["raw_p_value"])
