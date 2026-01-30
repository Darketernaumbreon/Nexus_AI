import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/api-client";
import { API } from "@/lib/endpoints";
import { Alert, AlertsResponse, PriorityLevel } from "@/types/alert";

const PRIORITY_ORDER: Record<PriorityLevel, number> = {
    P0: 0,
    P1: 1,
    P2: 2,
    P3: 3,
};

export function useAlerts() {
    return useQuery<Alert[]>({
        queryKey: ["alerts"],
        queryFn: async () => {
            try {
                const response = await apiClient.get<AlertsResponse>(API.ALERTS_ACTIVE);

                // Response is already unwrapped by interceptor
                const data = response as unknown as AlertsResponse;

                if (!data.alerts || data.alerts.length === 0) {
                    return [];
                }

                // Sort by priority (P0 first, P3 last)
                const sortedAlerts = data.alerts.sort((a: Alert, b: Alert) => {
                    return PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority];
                });

                return sortedAlerts;
            } catch (error) {
                console.error("Failed to fetch alerts:", error);
                return [];
            }
        },
        staleTime: 0, // Alerts are time-critical, no caching
        refetchInterval: 60 * 1000, // Poll every 60 seconds
        retry: false, // Safety-critical: don't retry on error
    });
}
