"use client";

import { useHealthCheck } from "@/hooks/use-health-check";
import { cn } from "@/lib/utils";

export function StatusBar() {
  const { systemOnline, systemReady, lastCheck } = useHealthCheck();

  return (
    <div className="h-8 border-t border-border bg-card px-4 flex items-center justify-between text-xs">
      <div className="flex items-center gap-4">
        {/* System Status Indicator */}
        <div className="flex items-center gap-2">
          <div
            className={cn(
              "h-2 w-2 rounded-full",
              systemOnline ? "bg-risk-low" : "bg-risk-high"
            )}
          />
          <span className="text-muted-foreground">
            System: {systemOnline ? "Online" : "Offline"}
          </span>
        </div>

        {/* Ready Status */}
        <div className="flex items-center gap-2">
          <div
            className={cn(
              "h-2 w-2 rounded-full",
              systemReady ? "bg-risk-low" : "bg-risk-medium"
            )}
          />
          <span className="text-muted-foreground">
            API: {systemReady ? "Ready" : "Degraded"}
          </span>
        </div>
      </div>

      {/* Last Check */}
      <span className="text-muted-foreground">
        Last check: {lastCheck.toLocaleTimeString()}
      </span>
    </div>
  );
}
