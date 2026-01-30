import { GeoJSONFeature } from "./geo";

// Alert zone types

export type HazardType = "flood" | "landslide";
export type SeverityLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type PriorityLevel = "P0" | "P1" | "P2" | "P3";

export interface AlertZone {
    hazard_type: HazardType;
    severity: SeverityLevel;
    confidence?: number;
    geometry: GeoJSONFeature;
    affected_area?: number;
    timestamp?: string;
}

export interface AlertZoneResponse {
    zones: AlertZone[];
    count: number;
}

// Alert types for Alerts Center

export interface Alert {
    alert_id: string;
    hazard_type: HazardType;
    severity: SeverityLevel;
    priority: PriorityLevel;
    message: string;
    recommended_action: string;
    valid_until: string;
    affected_radius_km: number;
    created_at?: string;
}

export interface AlertsResponse {
    alerts: Alert[];
    count: number;
}
