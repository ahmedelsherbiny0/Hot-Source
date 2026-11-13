/**
 * TypeScript Type Contracts for Trend Detective.
 * Mirroring FastAPI TrendAnalysisResponse schemas and frontend state models.
 */

export type SeasonFilter = "all" | "summer" | "winter";

export type CouplingStrength = "Strong" | "Moderate" | "Weak";

export type TrendTestName =
  | "Standard Mann-Kendall"
  | "Hamed-Rao Modified Mann-Kendall";

export interface MonthlySeriesPoint {
  date: string; // YYYY-MM
  raw_value: number;
  anomaly: number;
  is_outlier: boolean;
  qa_passed?: boolean;
}

export interface AnnualSeriesPoint {
  year: number;
  mean_value: number;
  mean_anomaly: number;
  months_count: number;
}

export interface OLSModel {
  slope: number;
  intercept: number;
  r_squared: number;
  ci_upper: number[];
  ci_lower: number[];
}

export interface TrendStatistics {
  sen_slope: number; // units / year
  cumulative_change: number; // sen_slope * delta_years
  p_value: number;
  z_stat: number;
  test_used: TrendTestName;
  is_significant: boolean; // p < 0.05
  cohens_d: number;
  welch_t?: number;
  welch_p?: number;
  lag1_autocorr: number;
  outlier_skew_warning: boolean; // True if OLS diverges from Sen's by > 30%
}

export interface PhysicalDriverAttribution {
  paired_variable: string;
  driver_name: string;
  correlation_r: number;
  coupling_strength: CouplingStrength;
  driver_reason: string;
}

export interface TrendAnalysisResponse {
  cache_key: string;
  variable_name: string;
  unit: string;
  dataset_source: string;
  region_label: string;
  cache_hit: boolean;
  series: MonthlySeriesPoint[];
  annual_series?: AnnualSeriesPoint[];
  ols: OLSModel;
  trend: TrendStatistics;
  physical_driver?: PhysicalDriverAttribution;
  driver_reason: string;
  updated_at?: string;
}

export interface BenchmarkRegion {
  id: string;
  name: string;
  lat: number;
  lon: number;
  bbox: [number, number, number, number]; // [South, West, North, East]
  default_variable: string;
  expected_driver: string;
  description: string;
}

export interface AnalysisRequest {
  lat: number;
  lon: number;
  variable: string;
  start_year: number;
  end_year: number;
  season: SeasonFilter;
  region_id?: string;
}

export interface DivergenceComparison {
  region_a: TrendAnalysisResponse;
  region_b: TrendAnalysisResponse;
  delta_sen_slope: number; // Sen's Slope (A) - Sen's Slope (B)
  delta_cumulative: number;
  divergence_narrative: string;
}

export interface MultiRegionScanItem {
  region_id: string;
  region_name: string;
  variable_name: string;
  unit: string;
  start_year: number;
  end_year: number;
  sen_slope: number;
  cumulative_change: number;
  raw_p_value: number;
  fdr_p_value: number;
  is_significant: boolean;
  test_used: TrendTestName;
  driver_reason: string;
}

export interface MultiRegionScanResponse {
  total_regions: number;
  significant_count: number;
  fdr_threshold: number;
  scanned_at: string;
  results: MultiRegionScanItem[];
}

export interface EarthSystemVariable {
  key: string;
  label: string;
  unit: string;
  category: "Hydrology" | "Thermal" | "Atmosphere" | "Biosphere";
  defaultSeason: SeasonFilter;
  description: string;
}
