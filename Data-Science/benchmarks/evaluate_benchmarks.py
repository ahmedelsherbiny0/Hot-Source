#!/usr/bin/env python3
"""
Benchmark Evaluation CLI Script.
Executes the full Trend Detective statistical pipeline across curated regional testbeds,
applies Benjamini-Hochberg FDR adjustments, and prints a scientific summary table.
"""

import sys
import os
from pathlib import Path

# Add Data-Science package to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from trend_detective.trend_engine import (
    analyze_time_series_trend,
    benjamini_hochberg_fdr,
)
from trend_detective.driver_attribution import attribute_physical_driver
from trend_detective.source_router import get_variable_time_series

BENCHMARKS = [
    {
        "id": "kansas",
        "name": "Kansas Plains (USA)",
        "lat": 38.5,
        "lon": -98.0,
        "variable": "surface_temp",
        "start_year": 2003,
        "end_year": 2025,
    },
    {
        "id": "arizona",
        "name": "Arizona Desert (USA)",
        "lat": 34.0,
        "lon": -111.8,
        "variable": "surface_temp",
        "start_year": 2003,
        "end_year": 2025,
    },
    {
        "id": "pearl_river",
        "name": "Pearl River Outflow (China)",
        "lat": 22.15,
        "lon": 113.7,
        "variable": "chlorophyll_a",
        "start_year": 2003,
        "end_year": 2025,
    },
    {
        "id": "mississippi_west",
        "name": "Mississippi River West (USA)",
        "lat": 29.05,
        "lon": -90.1,
        "variable": "chlorophyll_a",
        "start_year": 2003,
        "end_year": 2025,
    },
    {
        "id": "nile_delta",
        "name": "Nile Delta (Egypt)",
        "lat": 31.05,
        "lon": 31.0,
        "variable": "surface_temp",
        "start_year": 2000,
        "end_year": 2025,
    },
]

def main():
    print("=" * 80)
    print("  NASA SPACE APPS 2026 - TREND DETECTIVE STATISTICAL BENCHMARK EVALUATION")
    print("=" * 80)
    print()

    raw_results = []
    p_values = []

    for b in BENCHMARKS:
        data = get_variable_time_series(
            lat=b["lat"],
            lon=b["lon"],
            variable=b["variable"],
            start_year=b["start_year"],
            end_year=b["end_year"],
            region_id=b["id"],
        )
        series = data["series"]
        trend_res = analyze_time_series_trend(series, season="all")
        trend = trend_res["trend"]

        # Driver attribution
        driver = attribute_physical_driver(
            lat=b["lat"],
            lon=b["lon"],
            variable_key=b["variable"],
            primary_series=trend_res["series"],
            trend_stats=trend,
            start_year=b["start_year"],
            end_year=b["end_year"],
        )

        p_values.append(trend["p_value"])
        raw_results.append({
            "name": b["name"],
            "variable": b["variable"],
            "unit": data["unit"],
            "window": f"{b['start_year']}-{b['end_year']}",
            "sen_slope": trend["sen_slope"],
            "cumulative": trend["cumulative_change"],
            "raw_p": trend["p_value"],
            "test_used": trend["test_used"],
            "cohens_d": trend["cohens_d"],
            "autocorr": trend["lag1_autocorr"],
            "coupling": driver["coupling_strength"],
            "r": driver["correlation_r"],
        })

    # Benjamini-Hochberg FDR correction
    fdr_p_values, fdr_sig = benjamini_hochberg_fdr(p_values, alpha=0.05)

    print(f"{'Region':<26} {'Variable':<14} {'Sen Slope':<12} {'Raw p':<9} {'FDR p':<9} {'FDR Status':<10} {'Driver Coupling':<15}")
    print("-" * 105)

    for i, r in enumerate(raw_results):
        status = "SIGNIFICANT" if fdr_sig[i] else "NON-SIG"
        slope_str = f"{r['sen_slope']:+.4f} {r['unit']}/yr"
        driver_str = f"{r['coupling']} (r={r['r']:+.2f})"
        print(f"{r['name']:<26} {r['variable']:<14} {slope_str:<12} {r['raw_p']:<9.4f} {fdr_p_values[i]:<9.4f} {status:<10} {driver_str:<15}")

    print("-" * 105)
    print(f"Total Evaluated: {len(BENCHMARKS)} | FDR Significance Rate: {sum(fdr_sig)}/{len(BENCHMARKS)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
