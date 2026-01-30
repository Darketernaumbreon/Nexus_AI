"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

interface MapContainerProps {
    center?: [number, number];
    zoom?: number;
    children?: (map: maplibregl.Map | null) => React.ReactNode;
}

export function MapContainer({
    center = [92.9376, 26.2006], // Assam, NE India
    zoom = 7,
    children,
}: MapContainerProps) {
    const mapContainerRef = useRef<HTMLDivElement>(null);
    const mapRef = useRef<maplibregl.Map | null>(null);
    const [mapInstance, setMapInstance] = useState<maplibregl.Map | null>(null);

    useEffect(() => {
        // Initialize map only once
        if (mapRef.current || !mapContainerRef.current) return;

        mapRef.current = new maplibregl.Map({
            container: mapContainerRef.current,
            style: {
                version: 8,
                sources: {
                    "osm-tiles": {
                        type: "raster",
                        tiles: ["https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                        tileSize: 256,
                        attribution: '&copy; <a href="https://openstreetmap.org">OpenStreetMap</a> contributors',
                    },
                },
                layers: [
                    {
                        id: "osm-tiles",
                        type: "raster",
                        source: "osm-tiles",
                        minzoom: 0,
                        maxzoom: 19,
                    },
                ],
            },
            center,
            zoom,
        });

        // Add navigation controls
        mapRef.current.addControl(new maplibregl.NavigationControl(), "top-right");

        // Set map instance for children
        mapRef.current.on("load", () => {
            setMapInstance(mapRef.current);
        });

        // Cleanup on unmount
        return () => {
            if (mapRef.current) {
                mapRef.current.remove();
                mapRef.current = null;
                setMapInstance(null);
            }
        };
    }, [center, zoom]);

    return (
        <div className="relative w-full h-full">
            <div ref={mapContainerRef} className="absolute inset-0" />
            {/* Render children layers with map instance */}
            {children && children(mapInstance)}
        </div>
    );
}
