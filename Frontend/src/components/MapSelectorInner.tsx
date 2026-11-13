"use client";

import React, { useEffect, useRef, useState } from "react";
import L from "leaflet";
import { Crosshair, Layers } from "lucide-react";

export interface RegionLocation {
  id?: string;
  lat: number;
  lon: number;
  label?: string;
  subLabel?: string;
  bbox?: [number, number, number, number]; // [South, West, North, East]
}

export interface MapSelectorProps {
  regionA: RegionLocation;
  regionB?: RegionLocation | null;
  isDivergenceMode: boolean;
  activeTarget: "A" | "B";
  onTargetChange?: (target: "A" | "B") => void;
  onSelectCoordinates: (lat: number, lon: number, target: "A" | "B") => void;
  className?: string;
}

function formatCoords(lat: number, lon: number): string {
  const latDir = lat >= 0 ? "N" : "S";
  const lonDir = lon >= 0 ? "E" : "W";
  return `${Math.abs(lat).toFixed(2)}° ${latDir}, ${Math.abs(lon).toFixed(2)}° ${lonDir}`;
}

function formatBBoxString(bbox?: [number, number, number, number], lat?: number, lon?: number): string {
  if (bbox) {
    return `${bbox[0].toFixed(2)},${bbox[1].toFixed(2)},${bbox[2].toFixed(2)},${bbox[3].toFixed(2)}`;
  }
  if (lat !== undefined && lon !== undefined) {
    return `${(lat - 1.5).toFixed(2)},${(lon - 2.5).toFixed(2)},${(lat + 1.5).toFixed(2)},${(lon + 2.5).toFixed(2)}`;
  }
  return "30.40,50,30.40,50";
}

function createBoxLabelIcon(title: string, subLabel: string, coordsStr: string) {
  return L.divIcon({
    className: "region-box-label",
    html: `<div style="text-align: center; font-family: ui-sans-serif, system-ui, sans-serif; pointer-events: none; line-height: 1.15; padding: 2px;">
      <div style="font-weight: 800; font-size: 11px; letter-spacing: 0.05em; text-transform: uppercase; color: #020617;">${title}</div>
      <div style="font-weight: 600; font-size: 10px; color: #1e293b;">${subLabel}</div>
      <div style="font-family: monospace; font-size: 9px; font-weight: 600; color: #334155; margin-top: 1px;">${coordsStr}</div>
    </div>`,
    iconSize: [160, 48],
    iconAnchor: [80, 24],
  });
}

// 100% Free Public Tile URLs (Zero API key required, zero watermarks)
const ESRI_LIGHT_BASE =
  "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}";
const ESRI_LIGHT_REF =
  "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}";

const ESRI_DARK_BASE =
  "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}";
const ESRI_DARK_REF =
  "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}";

export default function MapSelectorInner({
  regionA,
  regionB,
  isDivergenceMode,
  activeTarget,
  onTargetChange,
  onSelectCoordinates,
  className = "h-full w-full",
}: MapSelectorProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const baseTileRef = useRef<any>(null);
  const refTileRef = useRef<any>(null);
  const bboxARef = useRef<any>(null);
  const labelARef = useRef<any>(null);
  const bboxBRef = useRef<any>(null);
  const labelBRef = useRef<any>(null);
  const [mapTheme, setMapTheme] = useState<"light" | "dark">("light");

  const activeTargetRef = useRef(activeTarget);
  const onSelectRef = useRef(onSelectCoordinates);

  useEffect(() => {
    activeTargetRef.current = activeTarget;
  }, [activeTarget]);

  useEffect(() => {
    onSelectRef.current = onSelectCoordinates;
  }, [onSelectCoordinates]);

  // Helper to load Esri tile layers
  const setTiles = (map: any, theme: "light" | "dark") => {
    if (baseTileRef.current) {
      map.removeLayer(baseTileRef.current);
      baseTileRef.current = null;
    }
    if (refTileRef.current) {
      map.removeLayer(refTileRef.current);
      refTileRef.current = null;
    }

    const baseUrl = theme === "light" ? ESRI_LIGHT_BASE : ESRI_DARK_BASE;
    const refUrl = theme === "light" ? ESRI_LIGHT_REF : ESRI_DARK_REF;

    baseTileRef.current = L.tileLayer(baseUrl, {
      maxZoom: 16,
      attribution: "&copy; Esri, DeLorme, NAVTEQ",
    }).addTo(map);

    refTileRef.current = L.tileLayer(refUrl, {
      maxZoom: 16,
      pane: "overlayPane",
    }).addTo(map);
  };

  // Initialize Map
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    // Center on United States default
    const map = L.map(containerRef.current, {
      center: [38.5, -98.0],
      zoom: 4,
      minZoom: 2,
      maxZoom: 16,
      zoomControl: true,
      attributionControl: false,
    });

    // Apply Esri Light Gray Canvas (No API key needed)
    setTiles(map, mapTheme);

    // Invalidate size after rendering to guarantee map renders without blank/grey tiles
    const timer1 = setTimeout(() => {
      map.invalidateSize();
    }, 100);
    const timer2 = setTimeout(() => {
      map.invalidateSize();
    }, 400);
    const timer3 = setTimeout(() => {
      map.invalidateSize();
    }, 1000);

    const handleResize = () => {
      map.invalidateSize();
    };
    window.addEventListener("resize", handleResize);

    // Click handler
    map.on("click", (e: any) => {
      const lat = Number(e.latlng.lat.toFixed(4));
      const lon = Number(e.latlng.lng.toFixed(4));
      onSelectRef.current(lat, lon, activeTargetRef.current);
    });

    mapRef.current = map;

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      window.removeEventListener("resize", handleResize);
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Handle tile theme toggle
  useEffect(() => {
    if (!mapRef.current) return;
    setTiles(mapRef.current, mapTheme);
  }, [mapTheme]);

  // Update Region A (Green)
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (bboxARef.current) {
      bboxARef.current.remove();
      bboxARef.current = null;
    }
    if (labelARef.current) {
      labelARef.current.remove();
      labelARef.current = null;
    }

    const bbox = regionA.bbox || [
      regionA.lat - 1.5,
      regionA.lon - 2.5,
      regionA.lat + 1.5,
      regionA.lon + 2.5,
    ];
    const bounds = [
      [bbox[0], bbox[1]],
      [bbox[2], bbox[3]],
    ];

    // Green rectangular overlay matching MacBook Air mockup
    bboxARef.current = L.rectangle(bounds, {
      color: "#22c55e",
      weight: 2,
      opacity: 0.9,
      fillColor: "#4ade80",
      fillOpacity: 0.45,
    }).addTo(map);

    // Center label inside rectangle
    const centerLat = (bbox[0] + bbox[2]) / 2;
    const centerLon = (bbox[1] + bbox[3]) / 2;
    const title = regionA.label || "KANSAS";
    const subLabel = regionA.subLabel || "Kansas, USA";
    const coordsStr = formatBBoxString(regionA.bbox, regionA.lat, regionA.lon);

    labelARef.current = L.marker([centerLat, centerLon], {
      icon: createBoxLabelIcon(title, subLabel, coordsStr),
      interactive: false,
    }).addTo(map);
  }, [regionA.lat, regionA.lon, regionA.bbox, regionA.label, regionA.subLabel]);

  // Update Region B (Lime/Yellow)
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (!isDivergenceMode || !regionB) {
      if (bboxBRef.current) {
        bboxBRef.current.remove();
        bboxBRef.current = null;
      }
      if (labelBRef.current) {
        labelBRef.current.remove();
        labelBRef.current = null;
      }
      return;
    }

    if (bboxBRef.current) {
      bboxBRef.current.remove();
      bboxBRef.current = null;
    }
    if (labelBRef.current) {
      labelBRef.current.remove();
      labelBRef.current = null;
    }

    const bbox = regionB.bbox || [
      regionB.lat - 1.5,
      regionB.lon - 2.5,
      regionB.lat + 1.5,
      regionB.lon + 2.5,
    ];
    const bounds = [
      [bbox[0], bbox[1]],
      [bbox[2], bbox[3]],
    ];

    // Lime / Yellow-Green rectangle matching MacBook Air - 2 mockup
    bboxBRef.current = L.rectangle(bounds, {
      color: "#84cc16",
      weight: 2,
      opacity: 0.9,
      fillColor: "#a3e635",
      fillOpacity: 0.45,
    }).addTo(map);

    const centerLat = (bbox[0] + bbox[2]) / 2;
    const centerLon = (bbox[1] + bbox[3]) / 2;
    const title = regionB.label || "ARIZONA";
    const subLabel = regionB.subLabel || "Arizona, USA";
    const coordsStr = formatBBoxString(regionB.bbox, regionB.lat, regionB.lon);

    labelBRef.current = L.marker([centerLat, centerLon], {
      icon: createBoxLabelIcon(title, subLabel, coordsStr),
      interactive: false,
    }).addTo(map);
  }, [
    isDivergenceMode,
    regionB?.lat,
    regionB?.lon,
    regionB?.bbox,
    regionB?.label,
    regionB?.subLabel,
  ]);

  return (
    <div
      className={`relative w-full h-full min-h-[500px] ${className}`}
      style={{ minHeight: "500px", height: "100%", width: "100%" }}
    >
      {/* Leaflet map container */}
      <div
        ref={containerRef}
        className="w-full h-full min-h-[500px]"
        style={{ minHeight: "500px", height: "100%", width: "100%" }}
      />

      {/* Floating Coordinate Badges on Map */}
      <div className="absolute top-4 left-4 z-[400] flex items-center gap-2 pointer-events-auto">
        <div className="bg-[#0b160b]/90 backdrop-blur-md border border-[#22c55e]/50 text-white px-3.5 py-1.5 rounded-full shadow-lg flex items-center gap-2 text-xs">
          <span className="w-2.5 h-2.5 rounded-full bg-[#22c55e]"></span>
          <span className="font-semibold">{regionA.label || "Region A"}:</span>
          <span className="font-mono text-slate-300">
            {formatCoords(regionA.lat, regionA.lon)}
          </span>
        </div>

        {isDivergenceMode && regionB && (
          <div className="bg-[#0b160b]/90 backdrop-blur-md border border-[#84cc16]/50 text-white px-3.5 py-1.5 rounded-full shadow-lg flex items-center gap-2 text-xs">
            <span className="w-2.5 h-2.5 rounded-full bg-[#a3e635]"></span>
            <span className="font-semibold">{regionB.label || "Region B"}:</span>
            <span className="font-mono text-slate-300">
              {formatCoords(regionB.lat, regionB.lon)}
            </span>
          </div>
        )}
      </div>

      {/* Map Tile & Target Switcher Controls */}
      <div className="absolute top-4 right-4 z-[400] flex items-center gap-2 pointer-events-auto">
        {/* Basemap Toggle */}
        <button
          onClick={() => setMapTheme((t) => (t === "light" ? "dark" : "light"))}
          className="bg-[#0b160b]/90 backdrop-blur-md border border-slate-700 hover:border-slate-500 text-slate-200 px-2.5 py-1.5 rounded-xl shadow-lg flex items-center gap-1.5 text-xs transition-colors"
          title="Toggle Map Style"
        >
          <Layers className="w-3.5 h-3.5 text-green-400" />
          <span className="capitalize">{mapTheme} Tiles</span>
        </button>

        {isDivergenceMode && onTargetChange && (
          <div className="bg-[#0b160b]/90 backdrop-blur-md border border-slate-700 p-1 rounded-xl flex items-center gap-1 shadow-lg text-xs">
            <button
              onClick={() => onTargetChange("A")}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                activeTarget === "A"
                  ? "bg-[#22c55e] text-slate-950 shadow"
                  : "text-slate-300 hover:text-white"
              }`}
            >
              Pin A (Green)
            </button>
            <button
              onClick={() => onTargetChange("B")}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                activeTarget === "B"
                  ? "bg-[#a3e635] text-slate-950 shadow"
                  : "text-slate-300 hover:text-white"
              }`}
            >
              Pin B (Lime)
            </button>
          </div>
        )}
      </div>

      {/* Bottom Hint */}
      <div className="absolute bottom-4 left-4 z-[400] pointer-events-none">
        <div className="bg-[#0b160b]/80 backdrop-blur-md border border-slate-800 px-3 py-1.5 rounded-lg text-[11px] text-slate-300 flex items-center gap-1.5 shadow">
          <Crosshair className="w-3.5 h-3.5 text-green-400" />
          <span>Click anywhere to adjust observation coordinates</span>
        </div>
      </div>
    </div>
  );
}
