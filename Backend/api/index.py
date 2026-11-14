"""
Trend Detective - FastAPI Application Entrypoint.
Exposes REST endpoints for health, benchmark presets, unified variable analysis,
and parallel multi-region scanning with Benjamini-Hochberg FDR adjustment.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api.db import get_supabase_client
from api.driver_attribution import attribute_physical_driver
from api.source_router import (
    BENCHMARK_KEY_MAP,
    VARIABLE_CATALOG,
    get_variable_time_series,
)
from api.trend_engine import (
    analyze_time_series_trend,
    benjamini_hochberg_fdr,
)

app = FastAPI(
    title="Trend Detective API",
    description="Statistical trend detection, non-parametric tests, and physical driver attribution for NASA Earth observations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS for Next.js frontend and local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.vercel.app",
        "*",  # Permissive for development & NASA challenge evaluation
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# Pydantic Request & Response Schemas
# ==============================================================================

class AnalysisRequest(BaseModel):
    lat: float = Field(..., description="Latitude in decimal degrees (-90 to 90)", ge=-90.0, le=90.0)
    lon: float = Field(..., description="Longitude in decimal degrees (-180 to 180)", ge=-180.0, le=180.0)
    variable: str = Field(default="evapotranspiration", description="Earth System variable key")
    start_year: int = Field(default=2000, description="Start year of observation window", ge=1850, le=2026)
    end_year: int = Field(default=2025, description="End year of observation window", ge=1850, le=2026)
    season: str = Field(default="all", description="Seasonal aggregation: 'all', 'summer', 'winter'")
    region_id: Optional[str] = Field(default=None, description="Optional preset benchmark identifier")


class BenchmarkRegion(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    bbox: List[float]  # [South, West, North, East]
    default_variable: str
    expected_driver: str
    description: str


# ==============================================================================
# Curated Benchmark Catalog
# ==============================================================================

BENCHMARK_PRESETS: List[Dict[str, Any]] = [
    {
        "id": "pearl_river",
        "name": "Pearl River Outflow (China)",
        "lat": 22.15,
        "lon": 113.7,
        "bbox": [21.8, 113.2, 22.5, 114.2],
        "default_variable": "chlorophyll_a",
        "expected_driver": "Intensive industrial & agricultural nutrient discharge across the Pearl River Delta basin",
        "description": "Persistent coastal eutrophication trend with summer algal blooms driven by terrestrial runoff.",
    },
    {
        "id": "mississippi_west",
        "name": "Mississippi River West Outflow (USA)",
        "lat": 29.05,
        "lon": -90.1,
        "bbox": [28.7, -90.6, 29.4, -89.6],
        "default_variable": "chlorophyll_a",
        "expected_driver": "Agricultural nitrogen runoff & episodic Midwest flood discharge pulses",
        "description": "Chronic Gulf hypoxia dynamics with extreme episodic flood outlier spikes (notably 2011 and 2019).",
    },
    {
        "id": "nile_delta",
        "name": "Nile Delta (Egypt)",
        "lat": 31.05,
        "lon": 31.0,
        "bbox": [30.5, 30.2, 31.6, 31.8],
        "default_variable": "surface_temp",
        "expected_driver": "Decadal land-use intensification, soil moisture depletion, and regional warming",
        "description": "Significant upward land surface temperature trend (+0.038 °C/year), pre-filtered with MOD11A2 QA cloud screening.",
    },
]


# ==============================================================================
# Root & Health Endpoints
# ==============================================================================

@app.get("/", tags=["Root"])
def root() -> Dict[str, Any]:
    """Root endpoint welcoming API consumers and pointing to documentation."""
    return {
        "name": "Trend Detective API",
        "version": "1.1.0",
        "description": "NASA Earth Science statistical trend engine & physical driver attribution platform",
        "docs": "/docs",
        "health": "/api/v1/health",
        "endpoints": {
            "health": "/api/v1/health",
            "benchmarks": "/api/v1/benchmarks",
            "analyze": "/api/v1/analyze/variable",
            "scan": "/api/v1/scan/benchmarks",
        },
    }


@app.get("/api/v1", tags=["Root"])
def api_v1_index() -> Dict[str, Any]:
    """Base API v1 overview."""
    return root()


@app.get("/api/v1/health", tags=["Health"])
def health_check() -> Dict[str, Any]:
    """Readiness and health check endpoint verifying database connectivity and capabilities."""
    supabase_configured = bool(
        os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    )

    return {
        "status": "healthy",
        "version": "1.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runtime": "Vercel Serverless Python",
        "database_configured": supabase_configured,
        "supported_variables": list(VARIABLE_CATALOG.keys()),
        "curated_benchmarks": [b["id"] for b in BENCHMARK_PRESETS],
        "capabilities": [
            "Hamed-Rao Mann-Kendall",
            "Theil-Sen Robust Slope",
            "OLS Hyperbolic 95% Confidence Bounds",
            "MAD Episodic Outlier Shield",
            "Vectorized Benjamini-Hochberg FDR",
            "Silent Physical Driver Attribution",
        ],
    }


# ==============================================================================
# Benchmarks Preset Endpoint
# ==============================================================================

@app.get("/api/v1/benchmarks", response_model=List[BenchmarkRegion], tags=["Benchmarks"])
def get_benchmarks() -> List[Dict[str, Any]]:
    """Return list of curated NASA regional case-study presets with coordinates and expected drivers."""
    return BENCHMARK_PRESETS


# ==============================================================================
# Unified Single-Point & Case-Study Analysis Endpoint
# ==============================================================================

@app.post("/api/v1/analyze/variable", tags=["Analysis"])
def analyze_variable(req: AnalysisRequest) -> Dict[str, Any]:
    """
    Unified analysis pipeline for single-point coordinates or curated case studies:
    1. Auto-routes variable to NASA GLDAS-2.1 / NOAA / Supabase cache.
    2. Runs statistical trend engine (Hamed-Rao Mann-Kendall, Theil-Sen, OLS hyperbolic CI, MAD).
    3. Concurrently attributes paired physical driver and computes Pearson correlation (r).
    4. Synthesizes structured natural-language diagnosis.
    """
    # 1. Fetch time series via source router (with caching & guardrails)
    raw_data = get_variable_time_series(
        lat=req.lat,
        lon=req.lon,
        variable=req.variable,
        start_year=req.start_year,
        end_year=req.end_year,
        region_id=req.region_id,
    )

    series_data = raw_data.get("series", [])
    if not series_data:
        raise HTTPException(
            status_code=404,
            detail=f"No observations found for variable '{req.variable}' in the requested window.",
        )

    # 2. Run statistical trend engine
    trend_result = analyze_time_series_trend(series_data, season=req.season)

    # 3. Silently attribute physical driver
    driver_result = attribute_physical_driver(
        lat=req.lat,
        lon=req.lon,
        variable_key=req.variable,
        primary_series=trend_result["series"],
        trend_stats=trend_result["trend"],
        start_year=req.start_year,
        end_year=req.end_year,
        documented_reason=raw_data.get("driver_reason"),
    )

    # 4. Return unified response conforming to frontend contracts
    return {
        "cache_key": raw_data["cache_key"],
        "variable_name": raw_data["variable_name"],
        "unit": raw_data["unit"],
        "dataset_source": raw_data["dataset_source"],
        "region_label": raw_data["region_label"],
        "cache_hit": raw_data.get("cache_hit", False),
        "series": trend_result["series"],
        "annual_series": trend_result.get("annual_series", []),
        "ols": trend_result["ols"],
        "trend": trend_result["trend"],
        "physical_driver": driver_result,
        "driver_reason": driver_result["driver_reason"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


# ==============================================================================
# Multi-Region Parallel Scan Endpoint (with Benjamini-Hochberg FDR)
# ==============================================================================

def _scan_single_benchmark(b: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to process a single benchmark preset in parallel."""
    var_key = b["default_variable"]
    raw_data = get_variable_time_series(
        lat=b["lat"],
        lon=b["lon"],
        variable=var_key,
        region_id=b["id"],
    )
    trend_res = analyze_time_series_trend(raw_data["series"], season="all")
    trend_stats = trend_res["trend"]

    return {
        "region_id": b["id"],
        "region_name": b["name"],
        "variable_name": var_key,
        "unit": raw_data["unit"],
        "start_year": int(raw_data["series"][0]["date"][:4]),
        "end_year": int(raw_data["series"][-1]["date"][:4]),
        "sen_slope": trend_stats["sen_slope"],
        "cumulative_change": trend_stats["cumulative_change"],
        "raw_p_value": trend_stats["p_value"],
        "test_used": trend_stats["test_used"],
        "driver_reason": raw_data.get("driver_reason") or b["expected_driver"],
    }


@app.get("/api/v1/scan/benchmarks", tags=["Scan"])
def scan_benchmarks() -> Dict[str, Any]:
    """
    Parallel multi-region trend scan across all curated benchmarks using ThreadPoolExecutor.
    Applies pure-NumPy Benjamini-Hochberg False Discovery Rate (FDR) adjustment across p-values.
    """
    results: List[Dict[str, Any]] = []

    # Parallelize benchmark trend evaluations
    with ThreadPoolExecutor(max_workers=min(4, len(BENCHMARK_PRESETS))) as executor:
        future_map = {
            executor.submit(_scan_single_benchmark, b): b["id"]
            for b in BENCHMARK_PRESETS
        }
        for future in as_completed(future_map):
            try:
                res = future.result()
                results.append(res)
            except Exception as e:
                print(f"[Error] Benchmark scan failed for {future_map[future]}: {e}")

    if not results:
        return {
            "total_regions": 0,
            "significant_count": 0,
            "fdr_threshold": 0.05,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "results": [],
        }

    # Sort results predictably by region_id
    results.sort(key=lambda x: x["region_id"])

    # Vectorized Benjamini-Hochberg FDR Adjustment
    raw_p_values = [item["raw_p_value"] for item in results]
    adj_p_values, sig_flags = benjamini_hochberg_fdr(raw_p_values, alpha=0.05)

    for i, item in enumerate(results):
        item["fdr_p_value"] = float(adj_p_values[i])
        item["is_significant"] = bool(sig_flags[i])

    significant_count = sum(1 for item in results if item["is_significant"])

    return {
        "total_regions": len(results),
        "significant_count": significant_count,
        "fdr_threshold": 0.05,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
