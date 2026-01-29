"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  CloudRain,
  CloudLightning,
  Droplets,
  Sun,
  X,
} from "lucide-react";
import type { WeatherAlert } from "@/types";
import { cn } from "@/lib/utils";

interface AlertBannerProps {
  alerts: WeatherAlert[];
  onDismiss?: (alertId: string) => void;
}

function getAlertIcon(type: WeatherAlert["type"]) {
  switch (type) {
    case "heavy_rain":
      return CloudRain;
    case "storm":
      return CloudLightning;
    case "flood":
      return Droplets;
    case "drought":
      return Sun;
    default:
      return AlertTriangle;
  }
}

function getSeverityStyles(severity: WeatherAlert["severity"]) {
  switch (severity) {
    case "critical":
      return "border-risk-high/50 bg-risk-high/10";
    case "high":
      return "border-risk-high/30 bg-risk-high/5";
    case "medium":
      return "border-risk-medium/30 bg-risk-medium/5";
    case "low":
      return "border-risk-low/30 bg-risk-low/5";
    default:
      return "border-border bg-secondary";
  }
}

function getSeverityBadgeVariant(severity: WeatherAlert["severity"]): "destructive" | "secondary" | "default" | "outline" {
  switch (severity) {
    case "critical":
    case "high":
      return "destructive";
    case "medium":
      return "secondary";
    default:
      return "default";
  }
}

export function AlertBanner({ alerts, onDismiss }: AlertBannerProps) {
  if (alerts.length === 0) {
    return (
      <div className="rounded-xl border border-risk-low/30 bg-risk-low/5 p-4 flex items-center gap-3">
        <div className="h-10 w-10 rounded-lg bg-risk-low/20 flex items-center justify-center">
          <Sun className="h-5 w-5 text-risk-low" />
        </div>
        <div>
          <p className="font-medium text-foreground">No Active Alerts</p>
          <p className="text-sm text-muted-foreground">
            Weather conditions are normal across all monitored regions
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => {
        const Icon = getAlertIcon(alert.type);

        return (
          <div
            key={alert.id}
            className={cn(
              "rounded-xl border p-4 transition-all",
              getSeverityStyles(alert.severity)
            )}
          >
            <div className="flex items-start gap-4">
              <div
                className={cn(
                  "h-10 w-10 rounded-lg flex items-center justify-center shrink-0",
                  alert.severity === "critical" || alert.severity === "high"
                    ? "bg-risk-high/20"
                    : alert.severity === "medium"
                    ? "bg-risk-medium/20"
                    : "bg-risk-low/20"
                )}
              >
                <Icon
                  className={cn(
                    "h-5 w-5",
                    alert.severity === "critical" || alert.severity === "high"
                      ? "text-risk-high"
                      : alert.severity === "medium"
                      ? "text-risk-medium"
                      : "text-risk-low"
                  )}
                />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h4 className="font-semibold text-foreground capitalize">
                    {alert.type.replace("_", " ")} Alert
                  </h4>
                  <Badge
                    variant={getSeverityBadgeVariant(alert.severity)}
                    className="rounded-lg text-xs capitalize"
                  >
                    {alert.severity}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  {alert.message}
                </p>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {alert.affected_regions.map((region) => (
                    <Badge
                      key={region}
                      variant="outline"
                      className="rounded-lg text-xs"
                    >
                      {region}
                    </Badge>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  Valid until:{" "}
                  {new Date(alert.valid_until).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
              {onDismiss && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 rounded-lg shrink-0"
                  onClick={() => onDismiss(alert.id)}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
