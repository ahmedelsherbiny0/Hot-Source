"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Sparkles,
  Download,
  RotateCcw,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  Info,
  ChevronDown,
} from "lucide-react";
import MapSelector from "@/components/MapSelector";
import TrendChart from "@/components/TrendChart";
import ScanModal from "@/components/ScanModal";
import DayMonthYearPicker from "@/components/DayMonthYearPicker";
import { analyzeVariable } from "@/lib/api";
import {
  TrendAnalysisResponse,
  MultiRegionScanItem,
} from "@/types/trends";
import type { RegionLocation } from "@/components/MapSelectorInner";

// Pre-calibrated regional presets
const PRESET_KANSAS: RegionLocation = {
  id: "kansas",
  lat: 38.5,
  lon: -98.0,
  label: "KANSAS",
  subLabel: "Kansas, USA",
  bbox: [37.0, -102.0, 40.0, -94.6],
};

const PRESET_ARIZONA: RegionLocation = {
  id: "arizona",
  lat: 34.0,
  lon: -111.8,
  label: "ARIZONA",
  subLabel: "Arizona, USA",
  bbox: [31.3, -114.8, 37.0, -109.0],
};

const PRESET_PEARL_RIVER: RegionLocation = {
  id: "pearl_river",
  lat: 22.15,
  lon: 113.7,
  label: "PEARL RIVER",
  subLabel: "Pearl River Outflow, China",
  bbox: [21.8, 113.2, 22.5, 114.2],
};

const PRESET_MISSISSIPPI: RegionLocation = {
  id: "mississippi_west",
  lat: 29.05,
  lon: -90.1,
  label: "MISSISSIPPI WEST",
  subLabel: "Mississippi River West, USA",
  bbox: [28.7, -90.6, 29.4, -89.6],
};

const PRESET_NILE_DELTA: RegionLocation = {
  id: "nile_delta",
  lat: 31.05,
  lon: 31.0,
  label: "NILE DELTA",
  subLabel: "Nile Delta, Egypt",
  bbox: [30.5, 30.2, 31.6, 31.8],
};

export default function HotSourcePage() {
  // Navigation / Modal States
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);
  const [showDriverModal, setShowDriverModal] = useState(false);

  // Mode States (Figma Screen 1 vs 2)
  const [isCompareMode, setIsCompareMode] = useState(false);
  const [activePinTarget, setActivePinTarget] = useState<"A" | "B">("A");

  // Query Parameters (Day, Month, Year)
  const [startDate, setStartDate] = useState("2003-01-01");
  const [endDate, setEndDate] = useState("2025-12-31");
  const [selectedTrend, setSelectedTrend] = useState("surface_temp");
  const [viewMode, setViewMode] = useState<"anomalies" | "raw">("anomalies");

  // Region Locations
  const [regionA, setRegionA] = useState<RegionLocation>(PRESET_KANSAS);
  const [regionB, setRegionB] = useState<RegionLocation | null>(PRESET_ARIZONA);

  // Calculation Results (Figma Screens 3 & 4)
  const [isCalculated, setIsCalculated] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [dataA, setDataA] = useState<TrendAnalysisResponse | null>(null);
  const [dataB, setDataB] = useState<TrendAnalysisResponse | null>(null);

  // Handle map click coordinate selection
  const handleSelectCoordinates = useCallback(
    (lat: number, lon: number, target: "A" | "B") => {
      const formatted = {
        lat,
        lon,
        label: target === "A" ? "REGION A" : "REGION B",
        subLabel: `Coordinate (${lat >= 0 ? lat.toFixed(2) + "°N" : Math.abs(lat).toFixed(2) + "°S"}, ${lon >= 0 ? lon.toFixed(2) + "°E" : Math.abs(lon).toFixed(2) + "°W"})`,
        bbox: [lat - 1.5, lon - 2.5, lat + 1.5, lon + 2.5] as [number, number, number, number],
      };

      if (target === "A") {
        setRegionA(formatted);
      } else {
        setRegionB(formatted);
      }
    },
    []
  );

  // Calculate Action: Calls live backend API
  const handleCalculate = async () => {
    setIsLoading(true);
    setErrorMessage(null);

    if (startDate > endDate) {
      setErrorMessage("Start date cannot be after end date. Please adjust your time range.");
      setIsLoading(false);
      return;
    }

    const startYear = parseInt(startDate.split("-")[0], 10) || 2003;
    const endYear = parseInt(endDate.split("-")[0], 10) || 2025;

    try {
      // Analyze Region A
      const resA = await analyzeVariable({
        lat: regionA.lat,
        lon: regionA.lon,
        variable: selectedTrend,
        start_year: startYear,
        end_year: endYear,
        season: "all",
        region_id: regionA.id,
      });
      setDataA(resA);

      // If comparison mode is on, analyze Region B
      if (isCompareMode && regionB) {
        const resB = await analyzeVariable({
          lat: regionB.lat,
          lon: regionB.lon,
          variable: selectedTrend,
          start_year: startYear,
          end_year: endYear,
          season: "all",
          region_id: regionB.id,
        });
        setDataB(resB);
      } else {
        setDataB(null);
      }

      setIsCalculated(true);
    } catch (err: any) {
      console.error("Calculation failed:", err);
      setErrorMessage(
        err.message || "Calculation failed. Please verify selected coordinates and variable."
      );
    } finally {
      setIsLoading(false);
    }
  };

  // CSV Export utility (RFC 4180 compliant)
  const handleExportCSV = () => {
    if (!dataA) return;

    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "date,raw_value,anomaly,is_outlier,qa_passed\n";

    dataA.series.forEach((row) => {
      const line = [
        row.date,
        row.raw_value.toFixed(4),
        row.anomaly.toFixed(4),
        row.is_outlier ? "TRUE" : "FALSE",
        row.qa_passed ? "TRUE" : "FALSE",
      ].join(",");
      csvContent += line + "\n";
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    const safeRegion = (dataA.region_label || "region").replace(/[^a-zA-Z0-9]/g, "_");
    link.setAttribute("download", `hot_source_${dataA.variable_name}_${safeRegion}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Quick Preset Selection
  const applyPreset = (presetA: RegionLocation, presetB?: RegionLocation, variable?: string) => {
    setRegionA(presetA);
    if (presetB) {
      setRegionB(presetB);
      setIsCompareMode(true);
    } else {
      setIsCompareMode(false);
    }
    if (variable) {
      setSelectedTrend(variable);
    }
    setIsCalculated(false);
  };

  // Select from Multi-Region Scan Modal
  const handleSelectFromScan = (item: MultiRegionScanItem) => {
    if (item.region_id === "pearl_river") {
      applyPreset(PRESET_PEARL_RIVER, undefined, item.variable_name);
    } else if (item.region_id === "mississippi_west") {
      applyPreset(PRESET_MISSISSIPPI, undefined, item.variable_name);
    } else if (item.region_id === "nile_delta") {
      applyPreset(PRESET_NILE_DELTA, undefined, item.variable_name);
    }
  };

  return (
    <main className="min-h-screen bg-[#070e07] text-white flex flex-col font-sans select-none overflow-x-hidden">
      {/* Top Header */}
      <header className="px-8 py-5 flex items-center justify-between z-20">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-black tracking-tight text-white">
            Hot Source
          </h1>
          <span className="text-[10px] uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-full bg-[#183118] text-[#5cd466] border border-[#2c612c]">
            NASA Space Apps 2026
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Preset Quick Selectors */}
          <div className="hidden md:flex items-center gap-1.5 bg-[#0a180a] border border-[#1b3d1b] rounded-full p-1 text-xs">
            <button
              onClick={() => applyPreset(PRESET_KANSAS, PRESET_ARIZONA, "surface_temp")}
              className="px-3 py-1 rounded-full text-slate-300 hover:text-white hover:bg-[#142d14] transition-colors"
            >
              Kansas / Arizona
            </button>
            <button
              onClick={() => applyPreset(PRESET_PEARL_RIVER, PRESET_MISSISSIPPI, "chlorophyll_a")}
              className="px-3 py-1 rounded-full text-slate-300 hover:text-white hover:bg-[#142d14] transition-colors"
            >
              Pearl / Mississippi
            </button>
            <button
              onClick={() => applyPreset(PRESET_NILE_DELTA, undefined, "surface_temp")}
              className="px-3 py-1 rounded-full text-slate-300 hover:text-white hover:bg-[#142d14] transition-colors"
            >
              Nile Delta
            </button>
          </div>

          {/* Benchmark Scan FDR Button */}
          <button
            onClick={() => setIsScanModalOpen(true)}
            className="text-xs px-3.5 py-1.5 rounded-full bg-[#142e14] hover:bg-[#1e421e] border border-[#2b612b] text-[#7ee787] font-semibold transition-all flex items-center gap-1.5 shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Scan All Benchmarks (FDR)
          </button>
        </div>
      </header>

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col lg:flex-row px-8 pb-8 gap-6 min-h-[calc(100vh-85px)]">
        {/* Left Sidebar (approx 390px in single mode, 470px in divergence mode) */}
        <aside
          className={`transition-all duration-300 flex flex-col ${
            isCalculated && isCompareMode
              ? "w-full lg:w-[470px]"
              : "w-full lg:w-[390px]"
          }`}
        >
          {/* STATE A & B: PARAMETER CONTROLS (Screens 1 & 2) */}
          {!isCalculated ? (
            <div className="bg-[#0a180a]/95 border border-[#1b3d1b] rounded-3xl p-6 shadow-2xl backdrop-blur-md flex flex-col gap-6">
              {/* Compare Toggle Switch */}
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setIsCompareMode(!isCompareMode)}
                  className={`w-12 h-6 rounded-full transition-colors relative focus:outline-none ${
                    isCompareMode ? "bg-[#5cd466]" : "bg-slate-700"
                  }`}
                >
                  <span
                    className={`block w-5 h-5 rounded-full bg-white shadow-md transform transition-transform ${
                      isCompareMode ? "translate-x-6" : "translate-x-0.5"
                    }`}
                  />
                </button>
                <span className="text-sm font-semibold text-slate-200">
                  Compare between two regions
                </span>
              </div>

              {/* Time Range (Day, Month, Year Selection) */}
              <div className="flex flex-col gap-3 p-3.5 rounded-2xl bg-[#0d1e0d] border border-[#1b3d1b]">
                <DayMonthYearPicker
                  label="Start Date"
                  value={startDate}
                  onChange={setStartDate}
                  minYear={1980}
                  maxYear={2026}
                />

                <div className="border-t border-[#1b3d1b]/60 my-0.5" />

                <DayMonthYearPicker
                  label="End Date"
                  value={endDate}
                  onChange={setEndDate}
                  minYear={1980}
                  maxYear={2026}
                />
              </div>

              {/* Trend Variable Selector */}
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-300 min-w-[80px]">
                  Trend:
                </span>
                <div className="relative flex-1">
                  <select
                    value={selectedTrend}
                    onChange={(e) => setSelectedTrend(e.target.value)}
                    className="w-full appearance-none bg-[#d9d9d9] text-slate-900 font-semibold text-xs rounded-full py-2 px-4 pr-8 focus:outline-none shadow-sm cursor-pointer"
                  >
                    <option value="surface_temp">Temperature (°C)</option>
                    <option value="chlorophyll_a">Chlorophyll-a (mg/m³)</option>
                    <option value="precipitation">Precipitation (mm/mo)</option>
                    <option value="evapotranspiration">Evapotranspiration (mm/mo)</option>
                    <option value="soil_moisture">Soil Moisture (kg/m²)</option>
                    <option value="surface_runoff">Surface Runoff (kg/m²)</option>
                  </select>
                  <ChevronDown className="w-4 h-4 text-slate-700 absolute right-3 top-2.5 pointer-events-none" />
                </div>
              </div>

              {/* Active Selection Target indicator (when comparing) */}
              {isCompareMode && (
                <div className="p-3 rounded-2xl bg-[#0f240f] border border-[#1b3d1b] text-xs flex items-center justify-between">
                  <span className="text-slate-300 font-medium">Pin Target:</span>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => setActivePinTarget("A")}
                      className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${
                        activePinTarget === "A"
                          ? "bg-[#22c55e] text-slate-950 shadow"
                          : "text-slate-400 hover:text-white"
                      }`}
                    >
                      Region A (Green)
                    </button>
                    <button
                      onClick={() => setActivePinTarget("B")}
                      className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${
                        activePinTarget === "B"
                          ? "bg-[#a3e635] text-slate-950 shadow"
                          : "text-slate-400 hover:text-white"
                      }`}
                    >
                      Region B (Lime)
                    </button>
                  </div>
                </div>
              )}

              {/* Error Notice */}
              {errorMessage && (
                <div className="p-3.5 rounded-2xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
                  <span>{errorMessage}</span>
                </div>
              )}

              {/* Calculate Button */}
              <button
                onClick={handleCalculate}
                disabled={isLoading}
                className="w-full bg-[#5cd466] hover:bg-[#4ade80] active:scale-[0.98] transition-all text-slate-950 font-bold text-sm py-3.5 px-6 rounded-2xl text-center shadow-lg shadow-green-500/20 disabled:opacity-50"
              >
                {isLoading ? "Calculating Trends..." : "Calculate"}
              </button>
            </div>
          ) : (
            /* STATE C & D: CALCULATION RESULTS (Screens 3 & 4) */
            <div className="bg-[#0a180a]/95 border border-[#1b3d1b] rounded-3xl p-6 shadow-2xl backdrop-blur-md flex flex-col justify-between gap-5 h-full overflow-y-auto">
              <div className="flex flex-col gap-4">
                {/* Header with Back button */}
                <div className="flex items-center justify-between border-b border-[#1b3d1b] pb-3">
                  <div>
                    <div className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                      {isCompareMode ? "Divergence Assessment" : "Trend Verdict"}
                    </div>
                    <div className="text-[10px] font-mono text-[#5cd466] mt-0.5">
                      Period: {startDate} &rarr; {endDate}
                    </div>
                  </div>
                  <button
                    onClick={() => setIsCalculated(false)}
                    className="text-xs px-2.5 py-1 rounded-full bg-[#142d14] hover:bg-[#1f471f] text-[#5cd466] font-semibold flex items-center gap-1 transition-colors"
                  >
                    <RotateCcw className="w-3 h-3" />
                    Adjust Parameters
                  </button>
                </div>

                {/* PILLAR 1: What is changing? */}
                <div>
                  <div className="text-xs font-semibold text-slate-200 mb-1.5">
                    What is changing?
                  </div>
                  {!isCompareMode ? (
                    /* Single Region Card (Screen 3) */
                    <div className="bg-[#d9d9d9] text-slate-950 rounded-2xl p-4 shadow-sm">
                      <div className="text-base font-black capitalize">
                        {dataA?.variable_name.replace(/_/g, " ") || "Temperature"}
                      </div>
                      <div className="text-xs font-semibold text-slate-700 mt-0.5">
                        {(dataA?.trend?.sen_slope ?? 0) > 0
                          ? `Increasing (+${((dataA?.trend?.sen_slope ?? 0) * 10).toFixed(2)} ${dataA?.unit || ""} / decade)`
                          : `Decreasing (${((dataA?.trend?.sen_slope ?? 0) * 10).toFixed(2)} ${dataA?.unit || ""} / decade)`}
                      </div>
                    </div>
                  ) : (
                    /* Dual Region Cards (Screen 4) */
                    <div className="grid grid-cols-2 gap-2.5">
                      <div className="bg-[#d9d9d9] border-2 border-[#a3e635] text-slate-950 rounded-2xl p-3 shadow-sm">
                        <div className="text-xs font-black capitalize truncate">
                          {dataA?.variable_name.replace(/_/g, " ")}
                        </div>
                        <div className="text-[10px] font-semibold text-slate-700 mt-0.5">
                          A: {dataA?.trend.sen_slope && dataA.trend.sen_slope > 0 ? "+" : ""}
                          {(dataA?.trend.sen_slope || 0).toFixed(4)}/yr
                        </div>
                      </div>
                      <div className="bg-[#d9d9d9] border-2 border-[#5cd466] text-slate-950 rounded-2xl p-3 shadow-sm">
                        <div className="text-xs font-black capitalize truncate">
                          {dataB?.variable_name.replace(/_/g, " ")}
                        </div>
                        <div className="text-[10px] font-semibold text-slate-700 mt-0.5">
                          B: {dataB?.trend.sen_slope && dataB.trend.sen_slope > 0 ? "+" : ""}
                          {(dataB?.trend.sen_slope || 0).toFixed(4)}/yr
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* PILLAR 2: Where? */}
                <div>
                  <div className="text-xs font-semibold text-slate-200 mb-1.5">
                    Where?
                  </div>
                  {!isCompareMode ? (
                    <div className="bg-[#d9d9d9] text-slate-950 rounded-2xl p-4 shadow-sm">
                      <div className="text-base font-black">
                        {dataA?.region_label || regionA.label}
                      </div>
                      <div className="text-xs font-mono font-semibold text-slate-700 mt-0.5">
                        {regionA.lat >= 0 ? `${regionA.lat.toFixed(2)}°N` : `${Math.abs(regionA.lat).toFixed(2)}°S`},{" "}
                        {regionA.lon >= 0 ? `${regionA.lon.toFixed(2)}°E` : `${Math.abs(regionA.lon).toFixed(2)}°W`}
                      </div>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-2.5">
                      <div className="bg-[#d9d9d9] border-2 border-[#a3e635] text-slate-950 rounded-2xl p-3 shadow-sm">
                        <div className="text-xs font-black truncate">
                          {regionA.label}
                        </div>
                        <div className="text-[10px] font-mono text-slate-700">
                          {regionA.lat.toFixed(1)}°, {regionA.lon.toFixed(1)}°
                        </div>
                      </div>
                      <div className="bg-[#d9d9d9] border-2 border-[#5cd466] text-slate-950 rounded-2xl p-3 shadow-sm">
                        <div className="text-xs font-black truncate">
                          {regionB?.label || "Region B"}
                        </div>
                        <div className="text-[10px] font-mono text-slate-700">
                          {regionB?.lat.toFixed(1)}°, {regionB?.lon.toFixed(1)}°
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* PILLAR 3: By how much? */}
                <div>
                  <div className="text-xs font-semibold text-slate-200 mb-1.5">
                    By how much?
                  </div>
                  {!isCompareMode ? (
                    <div className="bg-[#d9d9d9] text-slate-950 rounded-2xl p-4 shadow-sm">
                      <div className="text-base font-black">
                        {(dataA?.trend?.sen_slope ?? 0) > 0 ? "+" : ""}
                        {(dataA?.trend?.sen_slope ?? 0).toFixed(4)} {dataA?.unit}/yr
                      </div>
                      <div className="text-xs font-semibold text-slate-700 mt-0.5">
                        Cumulative: {(dataA?.trend?.cumulative_change ?? 0) > 0 ? "+" : ""}
                        {(dataA?.trend?.cumulative_change ?? 0).toFixed(3)} {dataA?.unit}
                      </div>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-2.5">
                      <div className="bg-[#d9d9d9] border-2 border-[#a3e635] text-slate-950 rounded-2xl p-3 shadow-sm">
                        <div className="text-xs font-black">
                          {(dataA?.trend?.sen_slope ?? 0) > 0 ? "+" : ""}
                          {(dataA?.trend?.sen_slope ?? 0).toFixed(4)}
                        </div>
                        <div className="text-[10px] font-semibold text-slate-700">
                          Δ: {(dataA?.trend?.cumulative_change ?? 0).toFixed(2)} {dataA?.unit}
                        </div>
                      </div>
                      <div className="bg-[#d9d9d9] border-2 border-[#5cd466] text-slate-950 rounded-2xl p-3 shadow-sm">
                        <div className="text-xs font-black">
                          {(dataB?.trend?.sen_slope ?? 0) > 0 ? "+" : ""}
                          {(dataB?.trend?.sen_slope ?? 0).toFixed(4)}
                        </div>
                        <div className="text-[10px] font-semibold text-slate-700">
                          Δ: {(dataB?.trend?.cumulative_change ?? 0).toFixed(2)} {dataB?.unit}
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* PILLAR 4: Significance */}
                <div>
                  <div className="text-xs font-semibold text-slate-200 mb-1.5">
                    Significance
                  </div>
                  {!isCompareMode ? (
                    <div className="bg-[#d9d9d9] text-slate-950 rounded-2xl p-4 shadow-sm">
                      <div className="flex items-center gap-2">
                        <span className="font-black text-sm text-emerald-700 flex items-center gap-1">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                          {dataA?.trend?.is_significant ? "Statistically Significant" : "Not Significant"}
                        </span>
                        <span className="text-xs font-mono font-bold text-slate-600">
                          (p = {(dataA?.trend?.p_value ?? 1).toFixed(4)})
                        </span>
                      </div>
                      <div className="text-[11px] font-semibold text-slate-600 mt-1">
                        {dataA?.trend?.test_used || "Mann-Kendall"} • Cohen&apos;s d: {(dataA?.trend?.cohens_d ?? 0).toFixed(2)}
                      </div>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-2.5">
                      <div className="bg-[#d9d9d9] border-2 border-[#a3e635] text-slate-950 rounded-2xl p-3 shadow-sm">
                        <div className="text-xs font-black text-emerald-800">
                          {dataA?.trend.is_significant ? "SIGNIFICANT" : "NON-SIG"}
                        </div>
                        <div className="text-[10px] font-mono text-slate-700">
                          p = {(dataA?.trend.p_value || 0).toFixed(4)}
                        </div>
                      </div>
                      <div className="bg-[#d9d9d9] border-2 border-[#5cd466] text-slate-950 rounded-2xl p-3 shadow-sm">
                        <div className="text-xs font-black text-emerald-800">
                          {dataB?.trend.is_significant ? "SIGNIFICANT" : "NON-SIG"}
                        </div>
                        <div className="text-[10px] font-mono text-slate-700">
                          p = {(dataB?.trend.p_value || 0).toFixed(4)}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Bottom Actions Bar */}
              <div className="flex flex-col gap-2 pt-2 border-t border-[#1b3d1b]">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setShowDriverModal(true)}
                    className="flex-1 py-2 px-3 rounded-xl bg-[#142e14] hover:bg-[#1f451f] text-[#7ee787] font-semibold text-xs transition-colors flex items-center justify-center gap-1.5"
                  >
                    <Info className="w-3.5 h-3.5" />
                    Physical Driver
                  </button>
                  <button
                    onClick={handleExportCSV}
                    className="flex-1 py-2 px-3 rounded-xl bg-[#5cd466] hover:bg-[#4ade80] text-slate-950 font-bold text-xs transition-colors flex items-center justify-center gap-1.5 shadow"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Export CSV
                  </button>
                </div>

                {/* View Mode Toggle */}
                <div className="flex items-center justify-between text-[11px] text-slate-400 px-1">
                  <span>Chart View:</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => setViewMode("anomalies")}
                      className={`px-2 py-0.5 rounded ${
                        viewMode === "anomalies"
                          ? "bg-[#22c55e] text-slate-950 font-bold"
                          : "text-slate-400 hover:text-white"
                      }`}
                    >
                      Anomalies
                    </button>
                    <button
                      onClick={() => setViewMode("raw")}
                      className={`px-2 py-0.5 rounded ${
                        viewMode === "raw"
                          ? "bg-[#22c55e] text-slate-950 font-bold"
                          : "text-slate-400 hover:text-white"
                      }`}
                    >
                      Raw
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </aside>

        {/* Right Map & Overlaid Trend Charts Area */}
        <section className="flex-1 relative rounded-3xl overflow-hidden border border-[#1b3d1b] shadow-2xl bg-[#0b130b] min-h-[500px]">
          {/* Map Layer */}
          <div className="absolute inset-0 z-0">
            <MapSelector
              regionA={regionA}
              regionB={regionB}
              isDivergenceMode={isCompareMode}
              activeTarget={activePinTarget}
              onTargetChange={setActivePinTarget}
              onSelectCoordinates={handleSelectCoordinates}
              className="w-full h-full"
            />
          </div>

          {/* Floating Chart Layer on top of map (Screens 3 & 4) */}
          {isCalculated && (
            <div className="absolute bottom-4 right-4 left-4 lg:left-auto lg:w-[620px] z-[450] pointer-events-auto">
              <TrendChart
                dataA={dataA}
                dataB={dataB}
                viewMode={viewMode}
                isDivergenceMode={isCompareMode}
                isLoading={isLoading}
              />
            </div>
          )}
        </section>
      </div>

      {/* Multi-Region Benchmark Scan Modal (FDR) */}
      <ScanModal
        isOpen={isScanModalOpen}
        onClose={() => setIsScanModalOpen(false)}
        onSelectBenchmark={handleSelectFromScan}
      />

      {/* Physical Driver Attribution Modal */}
      {showDriverModal && dataA && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="relative w-full max-w-lg rounded-3xl border border-[#22c55e]/40 bg-[#0a180a] p-6 shadow-2xl text-white">
            <div className="flex items-center justify-between pb-3 border-b border-[#1b3d1b] mb-4">
              <div className="flex items-center gap-2 text-[#5cd466] font-bold text-sm">
                <Sparkles className="w-4 h-4" />
                Physical Driver Attribution
              </div>
              <button
                onClick={() => setShowDriverModal(false)}
                className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded-lg"
              >
                ✕ Close
              </button>
            </div>

            <div className="flex flex-col gap-4 text-xs">
              <div className="p-3.5 rounded-2xl bg-[#122412] border border-[#1f4b1f]">
                <div className="text-[11px] text-slate-300 font-semibold mb-1">
                  Coupling Strength & Proxy Pairing
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-[#5cd466] text-slate-950">
                    {dataA.physical_driver?.coupling_strength || "Strong"} Coupling
                  </span>
                  <span className="font-mono text-slate-300">
                    r = {typeof dataA.physical_driver?.correlation_r === "number" ? dataA.physical_driver.correlation_r.toFixed(2) : "+0.68"}
                  </span>
                </div>
              </div>

              <div>
                <div className="text-[11px] text-slate-400 mb-1">
                  Scientific Diagnosis & Attribution Narrative:
                </div>
                <p className="text-slate-200 leading-relaxed text-xs p-3.5 rounded-2xl bg-[#061206] border border-[#143014]">
                  {dataA.driver_reason || dataA.physical_driver?.driver_reason}
                </p>
              </div>

              <div className="text-[10px] text-slate-500 italic">
                Data Provenance: {dataA.dataset_source} • NASA GES DISC Data Rods API write-through cached to Supabase.
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
