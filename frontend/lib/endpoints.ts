// Centralized API endpoint registry
// Single source of truth for all backend endpoints

export const API = {
    // Health check
    HEALTH: "/health/live",

    // Prediction endpoints
    FLOOD_PREDICT: "/predict/flood",
    LANDSLIDE_PREDICT: "/predict/landslide",

    // Alert endpoints
    ALERTS_ACTIVE: "/alerts/active",
    ALERTS_HISTORY: "/alerts/history",

    // Routing endpoints
    ROUTE_SAFE: "/routing/safe",

    // Geofence endpoints
    GEOFENCE_CHECK: "/geofence/check",

    // System Health
    PREDICTION_HEALTH: "/predict/health",
} as const;

// Type for endpoint keys
export type ApiEndpoint = (typeof API)[keyof typeof API];
