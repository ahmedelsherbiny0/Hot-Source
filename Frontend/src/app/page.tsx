import React from "react";
import {
  Activity,
  Compass,
  LineChart,
  ShieldCheck,
  Globe,
  Sliders,
  Layers,
  Sparkles,
} from "lucide-react";

export default function HomePage() {
  return (
    <main className="flex flex-col min-h-screen bg-slate-950 text-slate-100">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Globe className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
              Trend Detective
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-cyan-950 border border-cyan-500/30 text-cyan-400">
                NASA Challenge
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Earth Observation Statistical Engine & Physical Driver Attribution
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button className="text-xs px-3 py-1.5 rounded-md border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            Benchmark Presets
          </button>
          <button className="text-xs px-3 py-1.5 rounded-md bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold transition-colors flex items-center gap-1.5 shadow-sm shadow-cyan-500/20">
            <Sparkles className="w-3.5 h-3.5" />
            Scan Regions (FDR)
          </button>
        </div>
      </header>

      {/* Top 4-Pillar Summary Banner */}
      <section className="px-6 py-5 border-b border-slate-800 bg-slate-900/40">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Pillar 1 */}
          <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/50 flex flex-col justify-between">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="font-semibold uppercase tracking-wider text-slate-300">
                1. What Is Changing
              </span>
              <Activity className="w-4 h-4 text-cyan-400" />
            </div>
            <div>
              <div className="text-xl font-bold text-white">
                Evapotranspiration
              </div>
              <div className="text-xs text-cyan-400 mt-1">
                Increasing (+1.4 mm/decade)
              </div>
            </div>
          </div>

          {/* Pillar 2 */}
          <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/50 flex flex-col justify-between">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="font-semibold uppercase tracking-wider text-slate-300">
                2. Where
              </span>
              <Compass className="w-4 h-4 text-cyan-400" />
            </div>
            <div>
              <div className="text-xl font-bold text-white">Nile Delta</div>
              <div className="text-xs text-slate-400 mt-1">
                31.0°N, 31.0°E (Egypt)
              </div>
            </div>
          </div>

          {/* Pillar 3 */}
          <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/50 flex flex-col justify-between">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="font-semibold uppercase tracking-wider text-slate-300">
                3. By How Much
              </span>
              <LineChart className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <div className="text-xl font-bold text-white">
                +0.32 <span className="text-xs font-normal text-slate-400">mm/yr</span>
              </div>
              <div className="text-xs text-emerald-400 mt-1">
                Cumulative: +8.0 mm (2000–2025)
              </div>
            </div>
          </div>

          {/* Pillar 4 */}
          <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/50 flex flex-col justify-between">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="font-semibold uppercase tracking-wider text-slate-300">
                4. Statistically Significant?
              </span>
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-950 border border-emerald-500/30 text-emerald-400">
                  YES (p = 0.002)
                </span>
                <span className="text-xs text-slate-400">Hamed-Rao MK</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Cohen&apos;s d: 0.84 (Large Effect)
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Workspace Body */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Left Control Sidebar */}
        <aside className="w-full lg:w-80 border-r border-slate-800 bg-slate-900/30 p-5 flex flex-col gap-5 overflow-y-auto">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-cyan-400" />
              Investigation Controls
            </div>
            <span className="text-[10px] text-slate-500 font-mono">v1.0.0</span>
          </div>

          {/* Mode Toggle */}
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-2">
              Analysis Mode
            </label>
            <div className="grid grid-cols-2 gap-1.5 p-1 rounded-lg bg-slate-950 border border-slate-800">
              <button className="text-xs py-1.5 px-3 rounded-md bg-cyan-500 text-slate-950 font-semibold shadow-sm">
                Single Region
              </button>
              <button className="text-xs py-1.5 px-3 rounded-md text-slate-400 hover:text-slate-200">
                Divergence (A/B)
              </button>
            </div>
          </div>

          {/* Variable Selector */}
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-2">
              Earth System Variable
            </label>
            <select className="w-full text-xs bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-cyan-500">
              <option value="evapotranspiration">Evapotranspiration Flux (mm/month)</option>
              <option value="soil_moisture">Soil Moisture 0–10cm (kg/m²)</option>
              <option value="precipitation">Precipitation Rate (mm/month)</option>
              <option value="surface_runoff">Surface Runoff (kg/m²)</option>
              <option value="surface_temp">Land Surface Temperature (°C)</option>
              <option value="chlorophyll_a">Chlorophyll-a Concentration (mg/m³)</option>
            </select>
          </div>

          {/* Season Filter */}
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-2">
              Seasonal Aggregation
            </label>
            <div className="grid grid-cols-3 gap-1 p-1 rounded-lg bg-slate-950 border border-slate-800 text-center text-xs">
              <button className="py-1 rounded bg-slate-800 text-cyan-400 font-medium">
                All Months
              </button>
              <button className="py-1 rounded text-slate-400 hover:text-slate-200">
                Summer
              </button>
              <button className="py-1 rounded text-slate-400 hover:text-slate-200">
                Winter
              </button>
            </div>
          </div>

          {/* Year Range */}
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-2">
              Observation Window
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                defaultValue={2000}
                className="w-1/2 text-xs bg-slate-950 border border-slate-800 rounded-lg p-2 text-center text-slate-200"
              />
              <span className="text-slate-500 text-xs">to</span>
              <input
                type="number"
                defaultValue={2025}
                className="w-1/2 text-xs bg-slate-950 border border-slate-800 rounded-lg p-2 text-center text-slate-200"
              />
            </div>
          </div>

          {/* Physical Driver Attribution Box */}
          <div className="mt-auto p-4 rounded-xl border border-cyan-500/20 bg-cyan-950/20">
            <div className="flex items-center gap-1.5 text-xs font-bold text-cyan-400 mb-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              Physical Driver Attribution
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Evapotranspiration is strongly coupled (r = +0.72) with regional precipitation rate increases across the selected catchment.
            </p>
          </div>
        </aside>

        {/* Center / Right Content: Map and Chart Canvas */}
        <section className="flex-1 flex flex-col p-6 gap-6 overflow-y-auto">
          {/* Map Container */}
          <div className="h-72 w-full rounded-2xl border border-slate-800 bg-slate-900/50 overflow-hidden relative flex items-center justify-center">
            <div className="text-center text-slate-500 text-xs">
              <Globe className="w-8 h-8 mx-auto mb-2 opacity-40 text-cyan-400" />
              Leaflet Geospatial Map Container (Component: MapSelector.tsx)
              <div className="text-[11px] text-slate-600 mt-1">
                Dark CARTO Tiles • Region A (Cyan) • Region B (Amber)
              </div>
            </div>
          </div>

          {/* Trend Chart Container */}
          <div className="h-96 w-full rounded-2xl border border-slate-800 bg-slate-900/50 p-4 flex items-center justify-center">
            <div className="text-center text-slate-500 text-xs">
              <LineChart className="w-8 h-8 mx-auto mb-2 opacity-40 text-emerald-400" />
              Statistical Trend Chart Canvas (Component: TrendChart.tsx)
              <div className="text-[11px] text-slate-600 mt-1">
                Plotly Single-Axis • 95% Hyperbolic CI • Theil-Sen Line • MAD Outlier Diamond Markers
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
