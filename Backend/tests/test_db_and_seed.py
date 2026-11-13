"""
Unit tests for Supabase Schema Migration, Seeding Generators, and Cache Client.
"""

from pathlib import Path
from api.db import get_cached_series, save_cached_series
from scripts.seed_supabase import (
    generate_pearl_river_series,
    generate_mississippi_west_series,
    generate_nile_delta_lst_series,
    get_curated_benchmarks,
)


def test_schema_migration_file_exists_and_contains_required_definitions():
    """Verify scripts/migrate_schema.sql contains the required table and RLS policies."""
    sql_path = Path(__file__).resolve().parent.parent / "scripts" / "migrate_schema.sql"
    assert sql_path.exists(), "scripts/migrate_schema.sql must exist"

    content = sql_path.read_text(encoding="utf-8")
    assert "public.series_cache" in content
    assert "cache_key TEXT PRIMARY KEY" in content
    assert "dataset_source TEXT NOT NULL" in content
    assert "variable_name TEXT NOT NULL" in content
    assert "unit TEXT NOT NULL" in content
    assert "region_label TEXT NOT NULL" in content
    assert "driver_reason TEXT" in content
    assert "series_json JSONB NOT NULL" in content
    assert "ENABLE ROW LEVEL SECURITY" in content
    assert "Allow public read access" in content
    assert "service_role" in content


def test_pearl_river_generator_calibration():
    """Verify Pearl River chlorophyll-a series length, positive slope, and seasons."""
    series = generate_pearl_river_series()
    # 23 years (2003 to 2025 inclusive) * 12 months = 276
    assert len(series) == 276
    assert series[0]["date"] == "2003-01"
    assert series[-1]["date"] == "2025-12"

    # Check overall upward trend
    first_year_avg = sum(p["value"] for p in series[:12]) / 12.0
    last_year_avg = sum(p["value"] for p in series[-12:]) / 12.0
    assert last_year_avg > first_year_avg, "Pearl River must demonstrate eutrophication trend"


def test_mississippi_west_generator_contains_flood_outliers():
    """Verify Mississippi West series has injected 2011 and 2019 flood outlier spikes."""
    series = generate_mississippi_west_series()
    assert len(series) == 276

    val_by_date = {p["date"]: p["value"] for p in series}

    # Baseline values are ~2 to 5 mg/m^3
    assert val_by_date["2005-06"] < 6.0

    # 2011 Historic Flood spike
    assert val_by_date["2011-05"] > 10.0, "May 2011 must reflect Great Mississippi flood outlier"
    assert val_by_date["2011-06"] > 10.0

    # 2019 Prolonged Inundation spike
    assert val_by_date["2019-06"] > 10.0, "June 2019 must reflect Midwest flood outlier"


def test_nile_delta_lst_generator_calibration():
    """Verify Nile Delta MODIS LST series has Mediterranean seasonal swing and warming trend."""
    series = generate_nile_delta_lst_series()
    # 26 years (2000 to 2025 inclusive) * 12 months = 312
    assert len(series) == 312
    assert series[0]["date"] == "2000-01"
    assert series[-1]["date"] == "2025-12"

    # Summer peak (July) should be much warmer than winter (January)
    val_by_date = {p["date"]: p["value"] for p in series}
    assert val_by_date["2015-07"] > val_by_date["2015-01"] + 15.0

    # Overall warming drift
    first_era_mean = sum(p["value"] for p in series[:60]) / 60.0
    recent_era_mean = sum(p["value"] for p in series[-60:]) / 60.0
    assert recent_era_mean > first_era_mean


def test_get_curated_benchmarks_structure():
    """Verify benchmark payloads match Supabase public.series_cache expectations."""
    benchmarks = get_curated_benchmarks()
    assert len(benchmarks) == 3

    keys = {b["cache_key"] for b in benchmarks}
    assert "benchmark_pearl_river_chlorophyll_a" in keys
    assert "benchmark_mississippi_west_chlorophyll_a" in keys
    assert "benchmark_nile_delta_surface_temp" in keys

    for b in benchmarks:
        assert len(b["driver_reason"]) > 30, "Driver reason must be descriptive"
        assert len(b["series_json"]) > 200


def test_api_db_cache_manager():
    """Verify get_cached_series and save_cached_series work with local fallback."""
    # Test pre-seeded benchmark lookup
    cached = get_cached_series("benchmark_pearl_river_chlorophyll_a")
    assert cached is not None
    assert cached["variable_name"] == "chlorophyll_a"
    assert len(cached["series_json"]) == 276

    # Test unknown key
    assert get_cached_series("non_existent_key_xyz") is None

    # Test save and retrieve
    dummy_key = "test_custom_cache_entry"
    dummy_series = [{"date": "2020-01", "value": 15.4}]
    saved = save_cached_series(
        cache_key=dummy_key,
        dataset_source="NASA Test",
        variable_name="test_var",
        unit="test_unit",
        region_label="Test Region",
        driver_reason="Unit test explanation",
        series_json=dummy_series,
    )
    assert saved is True

    retrieved = get_cached_series(dummy_key)
    assert retrieved is not None
    assert retrieved["cache_key"] == dummy_key
    assert retrieved["variable_name"] == "test_var"
    assert retrieved["series_json"] == dummy_series
