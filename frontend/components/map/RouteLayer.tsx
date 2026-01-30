"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import { GeoJSONFeature } from "@/types/geo";
import { RouteStatus } from "@/types/route";

interface RouteLayerProps {
    map: maplibregl.Map | null;
    data: GeoJSONFeature | null;
    status?: RouteStatus;
}

const LAYER_ID = "safe-route";
const SOURCE_ID = "safe-route-source";

const STATUS_COLORS: Record<RouteStatus, string> = {
    SAFE: "#10b981", // Green
    CAUTION: "#eab308", // Yellow
    PARTIAL: "#f97316", // Orange
    BLOCKED: "#ef4444", // Red
};

export function RouteLayer({ map, data, status = "SAFE" }: RouteLayerProps) {
    const layerAddedRef = useRef(false);

    useEffect(() => {
        if (!map) return;

        // Wait for map to be fully loaded
        if (!map.isStyleLoaded()) {
            map.once("load", () => {
                addLayer();
            });
        } else {
            addLayer();
        }

        function addLayer() {
            if (!map || layerAddedRef.current) return;

            // Add source
            if (!map.getSource(SOURCE_ID)) {
                map.addSource(SOURCE_ID, {
                    type: "geojson",
                    data: data || {
                        type: "FeatureCollection",
                        features: [],
                    },
                });
            }

            // Add line layer
            if (!map.getLayer(LAYER_ID)) {
                map.addLayer({
                    id: LAYER_ID,
                    type: "line",
                    source: SOURCE_ID,
                    paint: {
                        "line-color": STATUS_COLORS[status],
                        "line-width": 4,
                        "line-opacity": 0.8,
                    },
                });
            }

            // Add border layer for better visibility
            if (!map.getLayer(`${LAYER_ID}-border`)) {
                map.addLayer({
                    id: `${LAYER_ID}-border`,
                    type: "line",
                    source: SOURCE_ID,
                    paint: {
                        "line-color": "#ffffff",
                        "line-width": 6,
                        "line-opacity": 0.5,
                    },
                });

                // Move route layer above border
                map.moveLayer(LAYER_ID);
            }

            layerAddedRef.current = true;
        }

        // Cleanup on unmount
        return () => {
            if (map && layerAddedRef.current) {
                if (map.getLayer(LAYER_ID)) {
                    map.removeLayer(LAYER_ID);
                }
                if (map.getLayer(`${LAYER_ID}-border`)) {
                    map.removeLayer(`${LAYER_ID}-border`);
                }
                if (map.getSource(SOURCE_ID)) {
                    map.removeSource(SOURCE_ID);
                }
                layerAddedRef.current = false;
            }
        };
    }, [map, status]);

    // Update data when it changes
    useEffect(() => {
        if (!map || !layerAddedRef.current) return;

        const source = map.getSource(SOURCE_ID) as maplibregl.GeoJSONSource;
        if (source) {
            source.setData(
                data || {
                    type: "FeatureCollection",
                    features: [],
                }
            );

            // Update line color based on status
            if (map.getLayer(LAYER_ID)) {
                map.setPaintProperty(LAYER_ID, "line-color", STATUS_COLORS[status]);
            }
        }
    }, [map, data, status]);

    return null;
}
