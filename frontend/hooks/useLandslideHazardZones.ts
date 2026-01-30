import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/api-client";
import { API } from "@/lib/endpoints";
import { GeoJSONFeatureCollection } from "@/types/geo";
import { AlertZoneResponse } from "@/types/alert";

export function useLandslideHazardZones() {
    return useQuery<GeoJSONFeatureCollection | null>({
        queryKey: ["landslide-hazard-zones"],
        queryFn: async () => {
            try {
                const response = await apiClient.get<AlertZoneResponse>(
                    "/alerts/zones?hazard=landslide"
                );

                // Response is already unwrapped by interceptor
                const data = response as unknown as AlertZoneResponse;

                // Convert alert zones to GeoJSON FeatureCollection
                if (!data || !data.zones || data.zones.length === 0) {
                    return null;
                }

                const features = data.zones.map((zone: any) => ({
                    type: "Feature" as const,
                    geometry: zone.geometry.geometry || zone.geometry,
                    properties: {
                        hazard_type: zone.hazard_type,
                        severity: zone.severity,
                        confidence: zone.confidence,
                        affected_area: zone.affected_area,
                        timestamp: zone.timestamp,
                    },
                }));

                return {
                    type: "FeatureCollection" as const,
                    features,
                };
            } catch (error) {
                console.error("Failed to fetch landslide hazard zones:", error);
                return null;
            }
        },
        staleTime: 60 * 1000, // 60 seconds
        retry: false, // Safety-critical: don't retry on error
    });
}
