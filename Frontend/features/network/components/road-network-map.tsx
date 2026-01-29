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
  const [zoom, setZoom] = useState(6);
  const [center] = useState({ lat: 20.5937, lng: 78.9629 }); // India center

  const handleZoomIn = useCallback(() => {
    setZoom((prev) => Math.min(prev + 1, 15));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom((prev) => Math.max(prev - 1, 3));
  }, []);

  const handleReset = useCallback(() => {
    setZoom(6);
  }, []);

  return (
    <Card className="relative h-full rounded-2xl shadow-soft overflow-hidden border-border">
      {/* Map Container - Visual Representation */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-100 to-slate-200">
        {/* Grid overlay for map effect */}
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: `
              linear-gradient(to right, var(--border) 1px, transparent 1px),
              linear-gradient(to bottom, var(--border) 1px, transparent 1px)
            `,
            backgroundSize: `${30 * (zoom / 6)}px ${30 * (zoom / 6)}px`,
          }}
        />

        {/* Simulated route lines */}
        <svg
          className="absolute inset-0 w-full h-full"
          viewBox="0 0 400 300"
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Route paths - simplified visual representation */}
          {routes.map((route, index) => {
            const isSelected = route.id === selectedRouteId;
            const pathData = [
              "M 50 150 Q 100 100, 150 120 T 250 100 T 350 150",
              "M 80 250 Q 120 200, 180 220 T 280 180 T 350 200",
              "M 100 80 Q 150 60, 200 100 T 300 80 T 380 120",
            ][index % 3];

            return (
              <g key={route.id}>
                <path
                  d={pathData}
                  fill="none"
                  stroke={getRiskColor(route.average_risk_score)}
                  strokeWidth={isSelected ? 6 : 4}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className={cn(
                    "cursor-pointer transition-all",
                    isSelected && "filter drop-shadow-lg"
                  )}
                  onClick={() => onRouteSelect?.(route.id)}
                  opacity={isSelected ? 1 : 0.7}
                />
                {/* Route segments with different risk colors */}
                {route.segments.map((segment, segIndex) => {
                  const segmentPathData = [
                    "M 50 150 Q 75 125, 100 135",
                    "M 100 135 Q 125 145, 150 120",
                    "M 150 120 Q 200 100, 250 100",
                  ][segIndex % 3];

                  return (
                    <path
                      key={segment.id}
                      d={segmentPathData}
                      fill="none"
                      stroke={getRiskColor(segment.risk_score)}
                      strokeWidth={isSelected ? 5 : 3}
                      strokeLinecap="round"
                      opacity={0}
                    />
                  );
                })}
              </g>
            );
          })}

          {/* City markers */}
          {[
            { x: 50, y: 150, name: "Delhi" },
            { x: 350, y: 150, name: "Jaipur" },
            { x: 80, y: 250, name: "Mumbai" },
            { x: 350, y: 200, name: "Pune" },
            { x: 100, y: 80, name: "Chennai" },
            { x: 380, y: 120, name: "Bangalore" },
          ].map((city) => (
            <g key={city.name}>
              <circle
                cx={city.x}
                cy={city.y}
                r="6"
                fill="var(--primary)"
                stroke="white"
                strokeWidth="2"
              />
              <text
                x={city.x}
                y={city.y - 12}
                textAnchor="middle"
                className="text-[10px] font-medium fill-foreground"
              >
                {city.name}
              </text>
            </g>
          ))}
        </svg>

        {/* Weather overlay hint */}
        {showWeatherLayer && (
          <div className="absolute top-4 left-4 bg-background/80 backdrop-blur-sm rounded-lg px-3 py-1.5">
            <span className="text-xs text-muted-foreground">
              Weather layer active
            </span>
          </div>
        )}
      </div>

      {/* Map Controls */}
      <div className="absolute top-4 right-4 flex flex-col gap-2">
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

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-card/90 backdrop-blur-sm rounded-xl p-3 shadow-soft">
        <p className="text-xs font-medium text-foreground mb-2">Risk Level</p>
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <div className="h-2 w-6 rounded-full bg-risk-low" />
            <span className="text-xs text-muted-foreground">Low (0-40)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-6 rounded-full bg-risk-medium" />
            <span className="text-xs text-muted-foreground">Medium (40-70)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-6 rounded-full bg-risk-high" />
            <span className="text-xs text-muted-foreground">High (70+)</span>
          </div>
        </div>
      </div>

      {/* Zoom level indicator */}
      <div className="absolute bottom-4 right-4 bg-card/90 backdrop-blur-sm rounded-lg px-3 py-1.5 shadow-soft">
        <span className="text-xs text-muted-foreground">Zoom: {zoom}x</span>
      </div>
    </Card>
  );
}
