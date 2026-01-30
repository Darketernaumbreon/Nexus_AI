"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import { GeoJSONFeatureCollection } from "@/types/geo";

interface FloodLayerProps {
    map: maplibregl.Map | null;
    data: GeoJSONFeatureCollection | null;
}

const LAYER_ID = "flood-zones";
const SOURCE_ID = "flood-zones-source";

export function FloodLayer({ map, data }: FloodLayerProps) {
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

            // Add fill layer
            if (!map.getLayer(LAYER_ID)) {
                map.addLayer({
                    id: LAYER_ID,
                    type: "fill",
                    source: SOURCE_ID,
                    paint: {
                        "fill-color": "#3b82f6", // Blue
                        "fill-opacity": 0.4,
                    },
                });
            }

            // Add border layer
            if (!map.getLayer(`${LAYER_ID}-border`)) {
                map.addLayer({
                    id: `${LAYER_ID}-border`,
                    type: "line",
                    source: SOURCE_ID,
                    paint: {
                        "line-color": "#1e40af", // Dark blue
                        "line-width": 2,
                    },
                });
            }

            // Add hover tooltip
            map.on("mouseenter", LAYER_ID, (e) => {
                map.getCanvas().style.cursor = "pointer";

                if (e.features && e.features[0]) {
                    const feature = e.features[0];
                    const severity = feature.properties?.severity || "UNKNOWN";

                    new maplibregl.Popup()
                        .setLngLat(e.lngLat)
                        .setHTML(
                            `
              <div style="padding: 8px;">
                <strong>Flood Risk Zone</strong><br/>
                Severity: <span style="color: #1e40af;">${severity}</span>
              </div>
            `
                        )
                        .addTo(map);
                }
            });

            map.on("mouseleave", LAYER_ID, () => {
                map.getCanvas().style.cursor = "";
            });

            layerAddedRef.current = true;
        }

        // Cleanup on unmount
        return () => {
            if (map && layerAddedRef.current) {
                if (map.getLayer(`${LAYER_ID}-border`)) {
                    map.removeLayer(`${LAYER_ID}-border`);
                }
                if (map.getLayer(LAYER_ID)) {
                    map.removeLayer(LAYER_ID);
                }
                if (map.getSource(SOURCE_ID)) {
                    map.removeSource(SOURCE_ID);
                }
                layerAddedRef.current = false;
            }
        };
    }, [map]);

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
        }
    }, [map, data]);

    return null;
}
