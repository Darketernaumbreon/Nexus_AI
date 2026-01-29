"use client";

import { useState, useEffect } from "react";
import type { HealthStatus } from "@/types";
import { HealthAPI } from "@/lib/api";

export function useHealthCheck(intervalMs: number = 30000) {
  const [healthStatus, setHealthStatus] = useState<HealthStatus>({
    isAlive: true,
    isReady: true,
    lastCheck: new Date(),
  });

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const status = await HealthAPI.checkHealth();
        setHealthStatus(status);
      } catch {
        setHealthStatus({
          isAlive: false,
          isReady: false,
          lastCheck: new Date(),
        });
      }
    };

    // Initial check
    checkHealth();

    // Set up polling
    const interval = setInterval(checkHealth, intervalMs);

    return () => clearInterval(interval);
  }, [intervalMs]);

  return {
    systemOnline: healthStatus.isAlive,
    systemReady: healthStatus.isReady,
    lastCheck: healthStatus.lastCheck,
  };
}
