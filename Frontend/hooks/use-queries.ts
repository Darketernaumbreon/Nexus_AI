import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { NetworkAPI, WeatherAPI, RiskAPI } from "@/lib/api";
import type { SimulationRequest } from "@/types";

// Query Keys
export const queryKeys = {
  routes: ["routes"] as const,
  routeDetail: (id: string) => ["routes", id] as const,
  weatherGrid: (regionId: string) => ["weather", "grid", regionId] as const,
  weatherAlerts: (regionId: string) => ["weather", "alerts", regionId] as const,
  simulation: (jobId: string) => ["simulation", jobId] as const,
  simulationResults: (jobId: string) => ["simulation", "results", jobId] as const,
  health: ["health"] as const,
};

// ============ Network Queries ============
export function useRoadNetwork() {
  return useQuery({
    queryKey: queryKeys.routes,
    queryFn: NetworkAPI.getRoadNetwork,
  });
}

export function useRouteDetail(routeId: string) {
  return useQuery({
    queryKey: queryKeys.routeDetail(routeId),
    queryFn: () => NetworkAPI.getRouteDetails(routeId),
    enabled: !!routeId,
  });
}

// ============ Weather Queries ============
export function useWeatherGrid() {
  return useQuery({
    queryKey: queryKeys.weatherGrid("india"),
    queryFn: WeatherAPI.getWeatherGrid,
    refetchInterval: 5 * 60 * 1000, // 5 minutes as per spec
  });
}

export function useWeatherAlerts() {
  return useQuery({
    queryKey: queryKeys.weatherAlerts("india"),
    queryFn: WeatherAPI.getAlerts,
    refetchInterval: 5 * 60 * 1000, // 5 minutes
  });
}

// ============ Risk Simulation Queries ============
export function useSimulationStatus(jobId: string | null, enabled = true) {
  return useQuery({
    queryKey: queryKeys.simulation(jobId || ""),
    queryFn: () => RiskAPI.getSimulationStatus(jobId!),
    enabled: !!jobId && enabled,
    refetchInterval: (query) => {
      // Poll every 2s while running, stop when complete
      const status = (query.state.data as any)?.status;
      if (status === "COMPLETED" || status === "FAILED") {
        return false;
      }
      return 2000; // 2 seconds as per spec
    },
  });
}

export function useSimulationResults(jobId: string | null) {
  return useQuery({
    queryKey: queryKeys.simulationResults(jobId || ""),
    queryFn: () => RiskAPI.getSimulationStatus(jobId!),
    enabled: !!jobId,
  });
}

// ============ Mutations ============
export function useStartSimulation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: SimulationRequest) => RiskAPI.startSimulation(request.region_id),
    onSuccess: (data) => {
      // Invalidate simulation queries when a new one starts
      queryClient.invalidateQueries({ queryKey: ["simulation"] });
    },
  });
}

// ============ Health Check ============
export function useHealthCheck() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: async () => {
      // Mock health check
      return {
        api: true,
        database: true,
        weather_service: Math.random() > 0.1,
      };
    },
    refetchInterval: 30 * 1000, // 30 seconds
  });
}
