import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/api-client";
import { SystemHealthData, SystemStatus } from "@/types/system";

import { API } from "@/lib/endpoints";

export function useSystemHealth() {
    return useQuery<SystemHealthData>({
        queryKey: ["system-health"],
        queryFn: async () => {
            const startTime = performance.now();

            try {
                // Call backend health endpoint
                const response = await apiClient.get(API.PREDICTION_HEALTH);
                const endTime = performance.now();
                const latencyMs = Math.round(endTime - startTime);

                // Determine status based on latency and response
                let status: SystemStatus = "ONLINE";
                if (latencyMs > 5000) {
                    status = "DEGRADED";
                }

                return {
                    status,
                    latencyMs,
                    lastChecked: new Date(),
                };
            } catch (error) {
                const endTime = performance.now();
                const latencyMs = Math.round(endTime - startTime);

                return {
                    status: "OFFLINE" as const,
                    latencyMs,
                    lastChecked: new Date(),
                };
            }
        },
        staleTime: 30 * 1000, // 30 seconds
        refetchInterval: 30 * 1000, // Poll every 30 seconds
        retry: 1,
    });
}
