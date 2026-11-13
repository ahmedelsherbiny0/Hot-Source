"""
Supabase PostgreSQL Database Client & Write-Through Cache Manager.
Manages series_cache queries, RLS authentication, and local fallback handling.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from supabase import Client, create_client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

# In-memory session cache for transient writes when database credentials are not present
_LOCAL_SESSION_CACHE: Dict[str, Dict[str, Any]] = {}


def get_supabase_client(use_service_role: bool = False) -> Optional[Any]:
    """
    Initialize Supabase Client.
    Uses SUPABASE_SERVICE_ROLE_KEY for write operations, or anon key for public reads.
    """
    if not HAS_SUPABASE:
        return None

    supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    if not supabase_url:
        return None

    if use_service_role:
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    else:
        key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not key:
        return None

    try:
        return create_client(supabase_url, key)
    except Exception as e:
        print(f"[Warning] Failed to initialize Supabase client: {e}")
        return None


def get_cached_series(cache_key: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached series by cache_key from Supabase public.series_cache.
    Falls back seamlessly to local session cache or pre-seeded JSON benchmarks.
    """
    # 1. Try Supabase query
    client = get_supabase_client(use_service_role=False)
    if client:
        try:
            res = client.table("series_cache").select("*").eq("cache_key", cache_key).execute()
            if res.data and len(res.data) > 0:
                row = res.data[0]
                return {
                    "cache_key": row["cache_key"],
                    "dataset_source": row["dataset_source"],
                    "variable_name": row["variable_name"],
                    "unit": row["unit"],
                    "region_label": row["region_label"],
                    "driver_reason": row.get("driver_reason"),
                    "series_json": row["series_json"],
                    "updated_at": row.get("updated_at"),
                    "source": "supabase"
                }
        except Exception as e:
            print(f"[Notice] Supabase cache read error for {cache_key}: {e}")

    # 2. Check transient in-memory cache
    if cache_key in _LOCAL_SESSION_CACHE:
        cached = _LOCAL_SESSION_CACHE[cache_key].copy()
        cached["source"] = "memory_cache"
        return cached

    # 3. Check pre-seeded filesystem backup in data/benchmarks/
    data_dir = Path(__file__).resolve().parent.parent / "data" / "benchmarks"
    json_path = data_dir / f"{cache_key}.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["source"] = "local_benchmark"
                return data
        except Exception:
            pass

    return None


def save_cached_series(
    cache_key: str,
    dataset_source: str,
    variable_name: str,
    unit: str,
    region_label: str,
    driver_reason: Optional[str],
    series_json: List[Dict[str, Any]],
) -> bool:
    """
    Persist series to Supabase public.series_cache with write-through cache logic.
    """
    record = {
        "cache_key": cache_key,
        "dataset_source": dataset_source,
        "variable_name": variable_name,
        "unit": unit,
        "region_label": region_label,
        "driver_reason": driver_reason,
        "series_json": series_json,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Store in local session cache immediately
    _LOCAL_SESSION_CACHE[cache_key] = record

    # Attempt Supabase write-through with service role
    client = get_supabase_client(use_service_role=True)
    if client:
        try:
            client.table("series_cache").upsert(record, on_conflict="cache_key").execute()
            return True
        except Exception as e:
            print(f"[Notice] Failed to write-through to Supabase for {cache_key}: {e}")
            return False

    return True
