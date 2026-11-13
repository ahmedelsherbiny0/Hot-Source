/**
 * API Client utilities for Trend Detective backend endpoints.
 */

import {
  AnalysisRequest,
  BenchmarkRegion,
  MultiRegionScanResponse,
  TrendAnalysisResponse,
} from "@/types/trends";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" ? "" : "http://127.0.0.1:8000");

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    let errorData = null;
    try {
      errorData = await response.json();
      if (errorData?.detail) {
        errorDetail =
          typeof errorData.detail === "string"
            ? errorData.detail
            : JSON.stringify(errorData.detail);
      }
    } catch {
      // Ignore JSON parse errors for non-JSON error bodies
    }

    throw new ApiError(errorDetail, response.status, errorData);
  }

  return response.json();
}

/**
 * Health & readiness check.
 */
export async function getHealth(): Promise<{
  status: string;
  version: string;
  runtime: string;
}> {
  return request("/api/v1/health");
}

/**
 * Fetch list of curated NASA benchmark regional presets.
 */
export async function getBenchmarks(): Promise<BenchmarkRegion[]> {
  return request("/api/v1/benchmarks");
}

/**
 * Submit single-point or regional case study for trend analysis & attribution.
 */
export async function analyzeVariable(
  req: AnalysisRequest
): Promise<TrendAnalysisResponse> {
  return request("/api/v1/analyze/variable", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/**
 * Run parallelized multi-region benchmark scan with FDR adjustment.
 */
export async function scanBenchmarks(): Promise<MultiRegionScanResponse> {
  return request("/api/v1/scan/benchmarks");
}
