import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/api-client";
import { API } from "@/lib/endpoints";
import { HealthCheckResponse } from "@/types/api";

interface HealthCheckResult {
    status: "ok" | "down";
    latencyMs: number;
    error?: string;
}

export function useHealthCheck() {
    return useQuery<HealthCheckResult>({
        queryKey: ["health"],
        queryFn: async () => {
            const startTime = performance.now();

            try {
                const response = await apiClient.get<HealthCheckResponse>(API.HEALTH);
                const endTime = performance.now();
                const latencyMs = Math.round(endTime - startTime);

                // Response is already unwrapped by interceptor
                const data = response as unknown as HealthCheckResponse;

                return {
                    status: (data.status === "ok" || data.status === "down")
                        ? data.status
                        : "ok",
                    latencyMs,
                };
            } catch (error) {
                const endTime = performance.now();
                const latencyMs = Math.round(endTime - startTime);

                return {
                    status: "down" as const,
                    latencyMs,
                    error: error instanceof Error ? error.message : "Unknown error",
                };
            }
        },
        staleTime: 60 * 1000, // 60 seconds
        refetchInterval: 60 * 1000, // Refetch every 60 seconds
    });
}
