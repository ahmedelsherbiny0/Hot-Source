"""
Trend Detective - FastAPI Application Entrypoint.
Optimized for Vercel Serverless Functions with CORS, health checks, and modular routing.
"""

from datetime import datetime, timezone
import os
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Trend Detective API",
    description="Statistical trend detection, non-parametric tests, and physical driver attribution for NASA Earth observations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS for Next.js frontend and external consumption
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.vercel.app",
        "*",  # Permissive for development & NASA hackathon evaluation
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def root() -> Dict[str, Any]:
    """Root endpoint welcoming API consumers and pointing to documentation."""
    return {
        "name": "Trend Detective API",
        "version": "1.0.0",
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
    """
    Readiness and health check endpoint for monitoring and uptime probes.
    Checks environment variables and service state.
    """
    supabase_configured = bool(
        os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    )

    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runtime": "Vercel Serverless Python",
        "database_configured": supabase_configured,
        "capabilities": [
            "Hamed-Rao Mann-Kendall",
            "Theil-Sen Robust Slope",
            "OLS Hyperbolic 95% Confidence Bounds",
            "MAD Episodic Outlier Shield",
            "Vectorized Benjamini-Hochberg FDR",
            "Silent Physical Driver Attribution",
        ],
    }
