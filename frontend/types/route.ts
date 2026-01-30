import { GeoJSONFeature } from "./geo";

// Route types

export type RouteStatus = "SAFE" | "CAUTION" | "PARTIAL" | "BLOCKED";

export interface RouteDetails {
    origin: { lat: number; lon: number };
    destination: { lat: number; lon: number };
    route_status: RouteStatus;
    distance_km: number;
    eta_minutes: number;
    avoided_hazards: string[];
    warnings: string[];
    geometry: GeoJSONFeature;
    // steps and segments are also returned but optional for now
}

export interface SafeRouteResponse {
    success: boolean;
    route: RouteDetails;
}

export interface RouteRequest {
    origin_lat: number;
    origin_lon: number;
    dest_lat: number;
    dest_lon: number;
}
