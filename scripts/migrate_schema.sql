-- Migration: Create public.series_cache Table and Configure Row-Level Security (RLS)
-- Description: Persists pre-calibrated NASA case studies and live NASA/NOAA fetches across serverless cold starts.

CREATE TABLE IF NOT EXISTS public.series_cache (
    cache_key TEXT PRIMARY KEY,
    dataset_source TEXT NOT NULL,
    variable_name TEXT NOT NULL,
    unit TEXT NOT NULL,
    region_label TEXT NOT NULL,
    driver_reason TEXT,
    series_json JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Optimization indexes for JSONB queries and variable/region lookups
CREATE INDEX IF NOT EXISTS idx_series_cache_var ON public.series_cache (variable_name);
CREATE INDEX IF NOT EXISTS idx_series_cache_region ON public.series_cache (region_label);
CREATE INDEX IF NOT EXISTS idx_series_cache_updated ON public.series_cache (updated_at DESC);

-- Enable Row-Level Security
ALTER TABLE public.series_cache ENABLE ROW LEVEL SECURITY;

-- 1. Public Anonymous Read Access: Any client can query cached series
DROP POLICY IF EXISTS "Allow public read access" ON public.series_cache;
CREATE POLICY "Allow public read access"
    ON public.series_cache
    FOR SELECT
    TO anon, authenticated
    USING (true);

-- 2. Restrict INSERT writes exclusively to the backend service role
DROP POLICY IF EXISTS "Allow service role insert access" ON public.series_cache;
CREATE POLICY "Allow service role insert access"
    ON public.series_cache
    FOR INSERT
    TO service_role
    WITH CHECK (true);

-- 3. Restrict UPDATE writes exclusively to the backend service role
DROP POLICY IF EXISTS "Allow service role update access" ON public.series_cache;
CREATE POLICY "Allow service role update access"
    ON public.series_cache
    FOR UPDATE
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 4. Restrict DELETE access exclusively to the backend service role
DROP POLICY IF EXISTS "Allow service role delete access" ON public.series_cache;
CREATE POLICY "Allow service role delete access"
    ON public.series_cache
    FOR DELETE
    TO service_role
    USING (true);
