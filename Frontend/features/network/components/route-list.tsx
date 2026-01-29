"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Route, AlertTriangle, CheckCircle, Info } from "lucide-react";
import type { RoutePolyline } from "@/types";
import { cn } from "@/lib/utils";

interface RouteListProps {
  routes: RoutePolyline[];
  selectedRouteId?: string | null;
  onRouteSelect?: (routeId: string) => void;
  isLoading?: boolean;
}

function getRiskBadgeVariant(
  riskScore: number
): "default" | "secondary" | "destructive" | "outline" {
  if (riskScore > 70) return "destructive";
  if (riskScore > 40) return "secondary";
  return "default";
}

function getRiskLabel(riskScore: number): string {
  if (riskScore > 70) return "High Risk";
  if (riskScore > 40) return "Medium Risk";
  return "Low Risk";
}

function getRiskIcon(riskScore: number) {
  if (riskScore > 70) return AlertTriangle;
  if (riskScore > 40) return Info;
  return CheckCircle;
}

export function RouteList({
  routes,
  selectedRouteId,
  onRouteSelect,
  isLoading,
}: RouteListProps) {
  if (isLoading) {
    return (
      <Card className="h-full rounded-2xl shadow-soft border-border">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-foreground">
            Routes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="h-20 rounded-xl animate-shimmer"
              />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full rounded-2xl shadow-soft border-border">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-foreground flex items-center gap-2">
            <Route className="h-5 w-5" />
            Routes
          </CardTitle>
          <Badge variant="outline" className="rounded-lg">
            {routes.length} total
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="p-2">
        <ScrollArea className="h-[calc(100vh-320px)]">
          <div className="space-y-2 p-2">
            {routes.map((route) => {
              const isSelected = route.id === selectedRouteId;
              const RiskIcon = getRiskIcon(route.average_risk_score);

              return (
                <button
                  key={route.id}
                  onClick={() => onRouteSelect?.(route.id)}
                  className={cn(
                    "w-full text-left p-4 rounded-xl border transition-all",
                    isSelected
                      ? "bg-primary/10 border-primary shadow-soft"
                      : "bg-card border-border hover:bg-accent hover:border-accent"
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-foreground truncate">
                        {route.name}
                      </h4>
                      <p className="text-sm text-muted-foreground mt-1">
                        {route.total_length_km.toFixed(1)} km •{" "}
                        {route.segments.length} segments
                      </p>
                    </div>
                    <Badge
                      variant={getRiskBadgeVariant(route.average_risk_score)}
                      className="rounded-lg shrink-0"
                    >
                      <RiskIcon className="h-3 w-3 mr-1" />
                      {Math.round(route.average_risk_score)}
                    </Badge>
                  </div>

                  {/* Source indicator */}
                  {route.source === "internal_postgis" && (
                    <div className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
                      <Info className="h-3 w-3" />
                      Using offline backup route
                    </div>
                  )}

                  {/* Segment breakdown */}
                  <div className="mt-3 flex gap-1">
                    {route.segments.map((segment) => (
                      <div
                        key={segment.id}
                        className="h-1.5 flex-1 rounded-full"
                        style={{
                          backgroundColor:
                            segment.risk_score > 70
                              ? "var(--risk-high)"
                              : segment.risk_score > 40
                              ? "var(--risk-medium)"
                              : "var(--risk-low)",
                        }}
                        title={`${segment.name}: Risk ${segment.risk_score}`}
                      />
                    ))}
                  </div>
                </button>
              );
            })}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
