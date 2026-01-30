
"use client";

import { useEffect, useMemo } from "react";
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Fix Leaflet Marker Icons in Next.js
// (Leaflet's default icon paths break in webpack)
const iconUrl = "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png";
const iconRetinaUrl = "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png";
const shadowUrl = "https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png";

const DefaultIcon = L.icon({
    iconUrl,
    iconRetinaUrl,
    shadowUrl,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    tooltipAnchor: [16, -28],
    shadowSize: [41, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;


interface LeafletMapInternalProps {
    routes: any[];
    onRouteSelect?: (id: string) => void;
    selectedRouteId?: string | null;
}

// Helper to auto-fit bounds
function BoundsUpdater({ routes }: { routes: any[] }) {
    const map = useMap();

    useEffect(() => {
        if (routes.length > 0) {
            // Collect all points
            const points = routes.flatMap(r => r.coordinates || []);
            if (points.length > 0) {
                // Leaflet expects [lat, lon], data is [lon, lat] or [lat, lon]?
                // GeoJSON is [lon, lat]. Leaflet is [lat, lon].
                // My WKT is POINT(LON LAT). My parser likely returns [lon, lat].
                // Let's assume input coordinates are [lon, lat] (GeoJSON standard)
                // We need to swap for Leaflet.
                const bounds = L.latLngBounds(points.map((p: any) => [p[1], p[0]]));
                map.fitBounds(bounds, { padding: [50, 50] });
            }
        }
    }, [routes, map]);

    return null;
}

export default function LeafletMapInternal({ routes, onRouteSelect, selectedRouteId }: LeafletMapInternalProps) {

    // Center on Guwahati by default
    const defaultCenter = [26.1445, 91.7362] as L.LatLngExpression;

    return (
        <MapContainer
            center={defaultCenter}
            zoom={10}
            style={{ height: "100%", width: "100%", borderRadius: "1rem" }}
            scrollWheelZoom={true}
        >
            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <BoundsUpdater routes={routes} />

            {routes.map((route) => {
                // Convert coords [lon, lat] -> [lat, lon]
                const positions = (route.coordinates || []).map((c: any) => [c[1], c[0]] as L.LatLngExpression);

                const isSelected = route.id === selectedRouteId;
                const color = route.average_risk_score > 70 ? "#ef4444" : // Risk High (Red)
                    route.average_risk_score > 40 ? "#f97316" : // Risk Medium (Orange)
                        "#10b981"; // Risk Low (Green)

                return (
                    <Polyline
                        key={route.id}
                        positions={positions}
                        pathOptions={{
                            color: color,
                            weight: isSelected ? 6 : 4,
                            opacity: isSelected ? 1 : 0.8
                        }}
                        eventHandlers={{
                            click: () => onRouteSelect?.(route.id)
                        }}
                    >
                        <Popup>
                            <div className="text-sm font-semibold">{route.name}</div>
                            <div className="text-xs">Risk Score: {route.average_risk_score}</div>
                            <div className="text-xs">Length: {route.total_length_km.toFixed(1)} km</div>
                        </Popup>
                    </Polyline>
                );
            })}
        </MapContainer>
    );
}
