// GeoJSON type definitions for map layers

export type GeoJSONFeature = GeoJSON.Feature;
export type GeoJSONFeatureCollection = GeoJSON.FeatureCollection;

// Hazard-specific GeoJSON types
export interface FloodZoneProperties {
    riskLevel: "low" | "medium" | "high";
    probability?: number;
    affectedArea?: number;
}

export interface LandslideZoneProperties {
    riskLevel: "low" | "medium" | "high";
    probability?: number;
    slope?: number;
}

export interface SafeRouteProperties {
    routeId: string;
    distance?: number;
    duration?: number;
}

export type FloodZoneFeature = GeoJSON.Feature<
    GeoJSON.Geometry,
    FloodZoneProperties
>;
export type LandslideZoneFeature = GeoJSON.Feature<
    GeoJSON.Geometry,
    LandslideZoneProperties
>;
export type SafeRouteFeature = GeoJSON.Feature<
    GeoJSON.Geometry,
    SafeRouteProperties
>;
