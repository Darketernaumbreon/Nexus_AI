"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Loader2, Clock, Activity } from "lucide-react";
import type { JobStatus } from "@/types";
import { REGIONS } from "@/types";

interface SimulationStatusProps {
  regionId: string;
  progress: number;
  estimatedTimeRemaining: number | null;
  status: JobStatus | null;
}

function getStatusLabel(status: JobStatus | null): string {
  switch (status) {
    case "QUEUED":
      return "Queued";
    case "PROCESSING":
      return "Processing";
    case "COMPLETED":
      return "Completed";
    case "FAILED":
      return "Failed";
    case "CANCELLED":
      return "Cancelled";
    default:
      return "Unknown";
  }
}

function getStatusMessage(status: JobStatus | null, regionName: string): string {
  switch (status) {
    case "QUEUED":
      return `Preparing analysis for ${regionName}...`;
    case "PROCESSING":
      return `Analyzing soil saturation and risk factors for ${regionName}...`;
    default:
      return "Processing...";
  }
}

export function SimulationStatus({
  regionId,
  progress,
  estimatedTimeRemaining,
  status,
}: SimulationStatusProps) {
  const region = REGIONS.find((r) => r.id === regionId);
  const regionName = region?.name || regionId;
  const progressPercent = Math.round(progress * 100);

  return (
    <Card className="rounded-2xl shadow-soft border-border overflow-hidden">
      {/* Shimmer overlay effect */}
      <div className="relative">
        <div className="absolute inset-0 animate-shimmer opacity-30" />
      </div>

      <CardContent className="pt-6 space-y-4">
        {/* Status Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <Loader2 className="h-5 w-5 text-primary animate-spin" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">
                Simulation Running
              </h3>
              <p className="text-sm text-muted-foreground">
                {getStatusMessage(status, regionName)}
              </p>
            </div>
          </div>
          <Badge variant="secondary" className="rounded-lg">
            {getStatusLabel(status)}
          </Badge>
        </div>

        {/* Progress Section */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Progress
            </span>
            <span className="font-medium text-foreground">
              {progressPercent}% Complete
            </span>
          </div>
          <Progress
            value={progressPercent}
            className="h-3 rounded-full"
          />
        </div>

        {/* ETA Display */}
        {estimatedTimeRemaining !== null && estimatedTimeRemaining > 0 && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>
              Estimated time remaining: {Math.ceil(estimatedTimeRemaining)}{" "}
              seconds
            </span>
          </div>
        )}

        {/* Processing Steps */}
        <div className="space-y-2 pt-2 border-t border-border">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Processing Steps
          </p>
          <div className="space-y-1.5">
            {[
              { label: "Loading road network data", threshold: 10 },
              { label: "Fetching weather conditions", threshold: 25 },
              { label: "Analyzing soil saturation", threshold: 50 },
              { label: "Calculating risk scores", threshold: 75 },
              { label: "Generating recommendations", threshold: 90 },
            ].map((step) => (
              <div
                key={step.label}
                className="flex items-center gap-2 text-sm"
              >
                <div
                  className={`h-2 w-2 rounded-full transition-colors ${
                    progressPercent >= step.threshold
                      ? "bg-risk-low"
                      : progressPercent >= step.threshold - 10
                      ? "bg-risk-medium animate-pulse"
                      : "bg-border"
                  }`}
                />
                <span
                  className={
                    progressPercent >= step.threshold
                      ? "text-foreground"
                      : "text-muted-foreground"
                  }
                >
                  {step.label}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Info Message */}
        <div className="rounded-lg bg-secondary p-3">
          <p className="text-xs text-muted-foreground">
            You can navigate away and return. Results will be cached in your
            session.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
