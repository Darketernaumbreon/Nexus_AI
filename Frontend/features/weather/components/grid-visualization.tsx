"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { WeatherCell } from "@/types";
import { cn } from "@/lib/utils";

interface GridVisualizationProps {
  cells: WeatherCell[];
  title?: string;
  description?: string;
}

function getRainfallColor(rainfall: number): string {
  if (rainfall > 100) return "bg-blue-700";
  if (rainfall > 75) return "bg-blue-600";
  if (rainfall > 50) return "bg-blue-500";
  if (rainfall > 25) return "bg-blue-400";
  if (rainfall > 10) return "bg-blue-300";
  return "bg-blue-200";
}

function getRainfallIntensity(rainfall: number): string {
  if (rainfall > 100) return "Very Heavy";
  if (rainfall > 75) return "Heavy";
  if (rainfall > 50) return "Moderate";
  if (rainfall > 25) return "Light";
  if (rainfall > 10) return "Very Light";
  return "Trace";
}

export function GridVisualization({
  cells,
  title = "IMD Weather Grid",
  description = "Real-time rainfall data visualization",
}: GridVisualizationProps) {
  // Arrange cells in a 3x3 grid
  const gridSize = 3;
  const gridCells = cells.slice(0, gridSize * gridSize);

  return (
    <Card className="rounded-2xl shadow-soft border-border">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-foreground">
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <TooltipProvider>
          <div className="grid grid-cols-3 gap-2">
            {gridCells.map((cell, index) => (
              <Tooltip key={cell.id}>
                <TooltipTrigger asChild>
                  <div
                    className={cn(
                      "aspect-square rounded-xl cursor-pointer transition-all hover:scale-105 flex items-center justify-center",
                      getRainfallColor(cell.rainfall_mm)
                    )}
                  >
                    <span className="text-white font-medium text-sm">
                      {Math.round(cell.rainfall_mm)}mm
                    </span>
                  </div>
                </TooltipTrigger>
                <TooltipContent className="rounded-xl">
                  <div className="space-y-1">
                    <p className="font-medium">Grid Cell {index + 1}</p>
                    <p className="text-xs text-muted-foreground">
                      Rainfall: {cell.rainfall_mm.toFixed(1)} mm (
                      {getRainfallIntensity(cell.rainfall_mm)})
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Temperature: {cell.temperature_c.toFixed(1)}°C
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Humidity: {cell.humidity_percent.toFixed(0)}%
                    </p>
                  </div>
                </TooltipContent>
              </Tooltip>
            ))}
          </div>
        </TooltipProvider>

        {/* Legend */}
        <div className="mt-4 pt-4 border-t border-border">
          <p className="text-xs font-medium text-foreground mb-2">
            Rainfall Intensity
          </p>
          <div className="flex gap-1">
            {[
              { label: "Trace", color: "bg-blue-200" },
              { label: "Light", color: "bg-blue-300" },
              { label: "Moderate", color: "bg-blue-500" },
              { label: "Heavy", color: "bg-blue-600" },
              { label: "Very Heavy", color: "bg-blue-700" },
            ].map((item) => (
              <div key={item.label} className="flex-1 text-center">
                <div className={cn("h-3 rounded", item.color)} />
                <span className="text-[10px] text-muted-foreground mt-1 block">
                  {item.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
