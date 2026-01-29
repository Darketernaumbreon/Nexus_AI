"use client";

import { useState, useEffect, useCallback } from "react";
import type { WeatherGrid, WeatherAlert } from "@/types";
import { WeatherAPI } from "@/lib/api";

export function useWeatherGrid(pollingInterval: number = 5 * 60 * 1000) {
  const [data, setData] = useState<WeatherGrid | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchWeatherGrid = useCallback(async () => {
    try {
      const grid = await WeatherAPI.getWeatherGrid();
      setData(grid);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err : new Error("Failed to fetch weather data")
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWeatherGrid();

    // AUTOMATED: Polling every 5 minutes
    const interval = setInterval(fetchWeatherGrid, pollingInterval);
    return () => clearInterval(interval);
  }, [fetchWeatherGrid, pollingInterval]);

  const refetch = useCallback(() => {
    setIsLoading(true);
    fetchWeatherGrid();
  }, [fetchWeatherGrid]);

  return {
    data,
    isLoading,
    error,
    refetch,
  };
}

export function useWeatherAlerts(pollingInterval: number = 5 * 60 * 1000) {
  const [alerts, setAlerts] = useState<WeatherAlert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchAlerts = useCallback(async () => {
    try {
      const data = await WeatherAPI.getAlerts();
      setAlerts(data);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err : new Error("Failed to fetch weather alerts")
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();

    // AUTOMATED: Polling every 5 minutes
    const interval = setInterval(fetchAlerts, pollingInterval);
    return () => clearInterval(interval);
  }, [fetchAlerts, pollingInterval]);

  return {
    alerts,
    isLoading,
    error,
    hasActiveAlerts: alerts.length > 0,
  };
}
