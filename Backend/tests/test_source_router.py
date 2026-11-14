"""
Unit tests for Unified Variable Auto-Router and Guardrails.
"""

import pytest
from fastapi import HTTPException

from api.source_router import (
    VARIABLE_CATALOG,
    decode_modis_lst_qa,
    get_variable_time_series,
    is_open_ocean,
    normalize_kelvin_to_celsius,
    validate_spatial_and_temporal_boundaries,
)


def test_variable_catalog_definitions():
    """Verify all domain variables have proper units, sources, and categories."""
    assert "evapotranspiration" in VARIABLE_CATALOG
    assert "soil_moisture" in VARIABLE_CATALOG
    assert "precipitation" in VARIABLE_CATALOG
    assert "surface_runoff" in VARIABLE_CATALOG
    assert "surface_temp" in VARIABLE_CATALOG
    assert "chlorophyll_a" in VARIABLE_CATALOG

    et = VARIABLE_CATALOG["evapotranspiration"]
    assert et["unit"] == "mm/month"
    assert et["is_land_only"] is True


def test_spatial_guardrail_blocks_open_ocean():
    """Verify that an open-ocean coordinate raises HTTP 422 on land-only variables."""
    # Mid-Pacific Ocean coordinates: 15.0°N, -150.0°W
    assert is_open_ocean(15.0, -150.0) is True

    with pytest.raises(HTTPException) as exc_info:
        validate_spatial_and_temporal_boundaries(
            lat=15.0, lon=-150.0, variable="evapotranspiration", start_year=2000, end_year=2020
        )
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["error_type"] == "spatial_boundary_error"


def test_spatial_guardrail_allows_land():
    """Verify terrestrial coordinates pass without error."""
    # Nile Delta coordinates: 31.0°N, 31.0°E
    assert is_open_ocean(31.0, 31.0) is False
    validate_spatial_and_temporal_boundaries(
        lat=31.0, lon=31.0, variable="evapotranspiration", start_year=2000, end_year=2020
    )


def test_temporal_guardrail_invalid_range():
    """Verify start_year > end_year raises HTTP 422."""
    with pytest.raises(HTTPException) as exc_info:
        validate_spatial_and_temporal_boundaries(
            lat=31.0, lon=31.0, variable="evapotranspiration", start_year=2022, end_year=2010
        )
    assert exc_info.value.status_code == 422


def test_noaa_temporal_fallback_for_pre_2000_precipitation():
    """Verify precipitation queries prior to 2000 automatically route to NOAA."""
    result = get_variable_time_series(
        lat=30.0, lon=-90.0, variable="precipitation", start_year=1980, end_year=2010
    )
    assert "NOAA" in result["dataset_source"]
    assert len(result["series"]) == 31 * 12  # 31 years of monthly data


def test_benchmark_cache_retrieval():
    """Verify pre-seeded benchmarks are returned directly with cache_hit = True."""
    result = get_variable_time_series(
        lat=22.15, lon=113.7, variable="chlorophyll_a", start_year=2003, end_year=2025, region_id="pearl_river"
    )
    assert result["cache_hit"] is True
    assert result["cache_key"] == "benchmark_pearl_river_chlorophyll_a"
    assert len(result["series"]) > 0


def test_write_through_cache_lifecycle():
    """Verify cache miss on first call and cache hit on repeat call."""
    lat, lon = 45.123, 12.456
    var = "surface_temp"

    # First call: cache miss
    res1 = get_variable_time_series(lat=lat, lon=lon, variable=var, start_year=2010, end_year=2015)
    assert res1["cache_hit"] is False

    # Second call: cache hit
    res2 = get_variable_time_series(lat=lat, lon=lon, variable=var, start_year=2010, end_year=2015)
    assert res2["cache_hit"] is True
    assert len(res1["series"]) == len(res2["series"])


def test_modis_qa_decoding():
    """Verify MODIS QA bit parser correctly flags cloud contamination."""
    # Good quality: bits 0-1 = 00 (integer 0)
    good = decode_modis_lst_qa(0)
    assert good["is_valid"] is True
    assert good["is_cloud_contaminated"] is False
    assert good["qa_level"] == "Good"

    # Cloud contaminated: bits 0-1 = 10 (integer 2)
    cloud = decode_modis_lst_qa(2)
    assert cloud["is_valid"] is False
    assert cloud["is_cloud_contaminated"] is True

    # Kelvin normalization
    assert normalize_kelvin_to_celsius(293.15) == 20.0


def test_multi_resource_adapters_exist_and_callable():
    """Verify that multiple data source adapters are exposed and functional."""
    from api.source_router import (
        fetch_upstream_nasa_power,
        fetch_upstream_noaa,
        fetch_upstream_cmr_granule,
        fetch_upstream_open_meteo,
    )
    assert callable(fetch_upstream_nasa_power)
    assert callable(fetch_upstream_noaa)
    assert callable(fetch_upstream_cmr_granule)
    assert callable(fetch_upstream_open_meteo)
