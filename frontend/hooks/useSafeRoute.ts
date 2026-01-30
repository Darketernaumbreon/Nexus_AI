import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/api-client";
import { API } from "@/lib/endpoints";
import { SafeRouteResponse, RouteRequest } from "@/types/route";

export function useSafeRoute(request: RouteRequest | null) {
    return useQuery<SafeRouteResponse | null>({
        queryKey: ["safe-route", request],
        queryFn: async () => {
            if (!request) {
                return null;
            }

            try {
                const response = await apiClient.get<SafeRouteResponse>(
                    `${API.ROUTE_SAFE}?origin_lat=${request.origin_lat}&origin_lon=${request.origin_lon}&dest_lat=${request.dest_lat}&dest_lon=${request.dest_lon}`
                );

                return response as unknown as SafeRouteResponse;
            } catch (error) {
                console.error("Failed to fetch safe route:", error);
                throw error;
            }
        },
        enabled: !!request, // Only fetch when request is provided
        staleTime: 5 * 60 * 1000, // 5 minutes
        retry: false, // Safety-critical: don't retry on error
    });
}
