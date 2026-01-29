"use client";

import { useState, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ZoomIn, ZoomOut, Maximize2, Layers } from "lucide-react";
import type { RoutePolyline } from "@/types";
import { cn } from "@/lib/utils";

interface RoadNetworkMapProps {
  routes: RoutePolyline[];
  selectedRouteId?: string | null;
  onRouteSelect?: (routeId: string) => void;
  showWeatherLayer?: boolean;
}

// Risk score to color mapping
function getRiskColor(riskScore: number): string {
  if (riskScore > 70) return "var(--risk-high)";
  if (riskScore > 40) return "var(--risk-medium)";
  return "var(--risk-low)";
}

function getRiskLabel(riskScore: number): "low" | "medium" | "high" {
  if (riskScore > 70) return "high";
  if (riskScore > 40) return "medium";
  return "low";
}

export function RoadNetworkMap({
  routes,
  selectedRouteId,
  onRouteSelect,
  showWeatherLayer = false,
}: RoadNetworkMapProps) {
  const [zoom, setZoom] = useState(1);

  // Calculate dynamic bounds
  const allCoords = routes.flatMap(r => r.coordinates || []);
  const hasData = allCoords.length > 0;

  const lons = hasData ? allCoords.map(c => c[0]) : [91.7, 91.8]; // Default split if empty
  const lats = hasData ? allCoords.map(c => c[1]) : [26.1, 26.2];

  const minLon = Math.min(...lons);
  const maxLon = Math.max(...lons);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);

  // Padding
  const lonSpan = maxLon - minLon || 0.1;
  const latSpan = maxLat - minLat || 0.1;
  const padX = lonSpan * 0.1;
  const padY = latSpan * 0.1;

  const project = (lon: number, lat: number) => {
    // Map to 400x300 SVG space with padding
    const x = ((lon - (minLon - padX)) / (lonSpan + 2 * padX)) * 400;
    const y = 300 - ((lat - (minLat - padY)) / (latSpan + 2 * padY)) * 300;
    return `${x} ${y}`;
  };

  // DEBUG: Visual confirmation of data
  // Remove this after verifying
  const debugInfo = {
    routeCount: routes.length,
    hasData,
    bounds: { minLon, maxLon, minLat, maxLat },
    sampleRoute: routes[0] ? { name: routes[0].name, coords: routes[0].coordinates?.length } : "None"
  };

  const handleZoomIn = useCallback(() => {
    setZoom((prev) => Math.min(prev + 0.5, 5));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom((prev) => Math.max(prev - 0.5, 1));
  }, []);

  const handleReset = useCallback(() => {
    setZoom(1);
  }, []);

  return (
    <Card className="relative h-full rounded-2xl shadow-soft overflow-hidden border-border">
      {/* Map Container - Visual Representation */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-100 to-slate-200">
        {/* Grid overlay */}
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: `
              linear-gradient(to right, var(--border) 1px, transparent 1px),
              linear-gradient(to bottom, var(--border) 1px, transparent 1px)
            `,
            backgroundSize: "40px 40px",
          }}
        />

        <svg
          className="absolute inset-0 w-full h-full transition-transform duration-300"
          style={{ transform: `scale(${zoom})` }}
          viewBox="0 0 400 300"
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Render Routes */}
          {routes.map((route) => {
            const isSelected = route.id === selectedRouteId;
            const coords = route.coordinates || [];

            if (coords.length < 2) return null;

            // Create SVG Path "M x y L x y ..."
            const d = coords.map((pt, i) =>
              `${i === 0 ? "M" : "L"} ${project(pt[0], pt[1])}`
            ).join(" ");

            return (
              <g key={route.id}>
                <path
                  d={d}
                  fill="none"
                  stroke={getRiskColor(route.average_risk_score)}
                  strokeWidth={isSelected ? 4 : 2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className={cn(
                    "cursor-pointer transition-all hover:stroke-[4px]",
                    isSelected && "filter drop-shadow-md"
                  )}
                  onClick={() => onRouteSelect?.(route.id)}
                  opacity={isSelected ? 1 : 0.8}
                />

                {/* Node Markers (Start/End) */}
                <circle cx={project(coords[0][0], coords[0][1]).split(' ')[0]}
                  cy={project(coords[0][0], coords[0][1]).split(' ')[1]}
                  r={isSelected ? 3 : 1.5} fill="var(--primary)" />
                <circle cx={project(coords[coords.length - 1][0], coords[coords.length - 1][1]).split(' ')[0]}
                  cy={project(coords[coords.length - 1][0], coords[coords.length - 1][1]).split(' ')[1]}
                  r={isSelected ? 3 : 1.5} fill="var(--primary)" />
              </g>
            );
          })}

          {!hasData && (
            <text x="200" y="150" textAnchor="middle" className="text-sm fill-muted-foreground">
              No geospatial data available
            </text>
          )}
        </svg>

        {/* Weather overlay hint */}
        {showWeatherLayer && (
          <div className="absolute top-4 left-4 bg-background/80 backdrop-blur-sm rounded-lg px-3 py-1.5 z-10">
            <span className="text-xs text-muted-foreground">
              Weather layer active
            </span>
          </div>
        )}
      </div>

      {/* Map Controls */}
      <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
        <Button
          variant="secondary"
          size="icon"
          className="h-9 w-9 rounded-lg shadow-soft bg-card"
          onClick={handleZoomIn}
        >
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button
          variant="secondary"
          size="icon"
          className="h-9 w-9 rounded-lg shadow-soft bg-card"
          onClick={handleZoomOut}
        >
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button
          variant="secondary"
          size="icon"
          className="h-9 w-9 rounded-lg shadow-soft bg-card"
          onClick={handleReset}
        >
          <Maximize2 className="h-4 w-4" />
        </Button>
      </div>

      {/* DEBUG OVERLAY */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-black/80 text-white p-2 rounded text-[10px] font-mono z-50 pointer-events-none max-w-xs overflow-hidden">
        <pre>{JSON.stringify(debugInfo, null, 2)}</pre>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-card/90 backdrop-blur-sm rounded-xl p-3 shadow-soft z-10">
        <p className="text-xs font-medium text-foreground mb-2">Risk Level</p>
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <div className="h-2 w-6 rounded-full bg-risk-low" />
            <span className="text-xs text-muted-foreground">Low</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-6 rounded-full bg-risk-medium" />
            <span className="text-xs text-muted-foreground">Medium</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-6 rounded-full bg-risk-high" />
            <span className="text-xs text-muted-foreground">High</span>
          </div>
        </div>
      </div>

      {/* Region Indicator - Dynamic */}
      <div className="absolute bottom-4 right-4 bg-card/90 backdrop-blur-sm rounded-lg px-3 py-1.5 shadow-soft z-10">
        <span className="text-xs font-medium">
          {hasData ? "Region: North East (Live)" : "No Data"}
        </span>
      </div>
    </Card>
  );
}
