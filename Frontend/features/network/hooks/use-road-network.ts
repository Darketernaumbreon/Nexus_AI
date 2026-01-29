"use client";

import { useState, useEffect, useCallback } from "react";
import type { RoadNetwork, RoutePolyline } from "@/types";
import { NetworkAPI } from "@/lib/api";

export function useRoadNetwork() {
  const [data, setData] = useState<RoadNetwork | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchRoadNetwork = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const network = await NetworkAPI.getRoadNetwork();
      setData(network);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to fetch road network"));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRoadNetwork();
  }, [fetchRoadNetwork]);

  const refetch = useCallback(() => {
    fetchRoadNetwork();
  }, [fetchRoadNetwork]);

  return {
    data,
    isLoading,
    error,
    refetch,
  };
}

export function useRouteDetails(routeId: string | null) {
  const [data, setData] = useState<RoutePolyline | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!routeId) {
      setData(null);
      return;
    }

    const fetchRoute = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const route = await NetworkAPI.getRouteDetails(routeId);
        setData(route);
      } catch (err) {
        setError(err instanceof Error ? err : new Error("Failed to fetch route details"));
      } finally {
        setIsLoading(false);
      }
    };

    fetchRoute();
  }, [routeId]);

  return {
    data,
    isLoading,
    error,
  };
}
