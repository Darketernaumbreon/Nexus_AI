"use client";

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import {
  MapPin,
  Route,
  AlertTriangle,
  Ruler,
  Layers,
  Clock,
} from "lucide-react";
import type { RoutePolyline } from "@/types";

interface NodeDetailsProps {
  route: RoutePolyline | null;
  isOpen: boolean;
  onClose: () => void;
}

function getRiskColor(riskScore: number): string {
  if (riskScore > 70) return "text-risk-high";
  if (riskScore > 40) return "text-risk-medium";
  return "text-risk-low";
}

function getRiskBgColor(riskScore: number): string {
  if (riskScore > 70) return "bg-risk-high";
  if (riskScore > 40) return "bg-risk-medium";
  return "bg-risk-low";
}

export function NodeDetails({ route, isOpen, onClose }: NodeDetailsProps) {
  if (!route) return null;

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="w-[400px] sm:w-[540px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2 text-foreground">
            <Route className="h-5 w-5" />
            {route.name}
          </SheetTitle>
          <SheetDescription>
            Detailed route information and risk assessment
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Overview Stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-xl bg-secondary p-4">
              <div className="flex items-center gap-2 text-muted-foreground mb-1">
                <Ruler className="h-4 w-4" />
                <span className="text-sm">Total Length</span>
              </div>
              <p className="text-2xl font-bold text-foreground">
                {route.total_length_km.toFixed(1)} km
              </p>
            </div>
            <div className="rounded-xl bg-secondary p-4">
              <div className="flex items-center gap-2 text-muted-foreground mb-1">
                <AlertTriangle className="h-4 w-4" />
                <span className="text-sm">Avg. Risk</span>
              </div>
              <p
                className={`text-2xl font-bold ${getRiskColor(
                  route.average_risk_score
                )}`}
              >
                {Math.round(route.average_risk_score)}%
              </p>
            </div>
          </div>

          {/* Risk Progress */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-foreground">
                Overall Risk Level
              </span>
              <span
                className={`text-sm font-medium ${getRiskColor(
                  route.average_risk_score
                )}`}
              >
                {route.average_risk_score > 70
                  ? "High"
                  : route.average_risk_score > 40
                    ? "Medium"
                    : "Low"}
              </span>
            </div>
            <div className="h-3 w-full rounded-full bg-secondary overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${getRiskBgColor(
                  route.average_risk_score
                )}`}
                style={{ width: `${route.average_risk_score}%` }}
              />
            </div>
          </div>

          <Separator />

          {/* Source Info */}
          <div className="flex items-center gap-3 rounded-xl bg-secondary p-4">
            <Layers className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium text-foreground">Data Source</p>
              <p className="text-xs text-muted-foreground">
                {route.source === "osrm"
                  ? "OSRM Routing Engine"
                  : "Internal PostGIS (Offline)"}
              </p>
            </div>
            {route.source === "internal_postgis" && (
              <Badge variant="outline" className="ml-auto rounded-lg">
                Offline
              </Badge>
            )}
          </div>

          <Separator />

          {/* Segments */}
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-3">
              Route Segments ({route.segments.length})
            </h4>
            <div className="space-y-3">
              {route.segments.map((segment, index) => (
                <div
                  key={segment.id}
                  className="rounded-xl border border-border p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-foreground">
                        {segment.name}
                      </p>
                      <p className="text-sm text-muted-foreground mt-1">
                        {segment.length_km?.toFixed(1) || "0.0"} km
                        {segment.surface_type &&
                          ` • ${segment.surface_type}`}
                      </p>
                    </div>
                    <Badge
                      variant={
                        segment.risk_score > 70
                          ? "destructive"
                          : segment.risk_score > 40
                            ? "secondary"
                            : "default"
                      }
                      className="rounded-lg"
                    >
                      Risk: {segment.risk_score}
                    </Badge>
                  </div>
                  <div className="mt-3">
                    <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
                      <div
                        className={`h-full rounded-full ${getRiskBgColor(
                          segment.risk_score
                        )}`}
                        style={{ width: `${segment.risk_score}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
