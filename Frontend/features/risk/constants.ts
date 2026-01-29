/**
 * Risk Simulation Feature - Constants
 *
 * Configuration constants for risk analysis and simulations
 */

/**
 * Risk level color mapping
 */
export const RISK_LEVEL_COLORS = {
  low: '#10b981',      // Green
  medium: '#f59e0b',   // Amber
  high: '#ef4444',     // Red
  critical: '#7c2d12', // Dark red
} as const;

/**
 * Risk level numerical thresholds
 * Risk scores (0-1) mapped to levels
 */
export const RISK_LEVEL_THRESHOLDS = {
  low: 0.25,
  medium: 0.5,
  high: 0.75,
  critical: 1.0,
} as const;

/**
 * Risk factor default weights
 * Used in risk score calculations
 */
export const DEFAULT_RISK_FACTOR_WEIGHTS = {
  weather: 0.25,
  traffic: 0.20,
  infrastructure: 0.20,
  environmental: 0.15,
  accident: 0.15,
  construction: 0.05,
} as const;

/**
 * Weather scenario configurations
 */
export const WEATHER_SCENARIOS = {
  clear: {
    label: 'Clear',
    description: 'Sunny with good visibility',
    riskModifier: 0.8,
  },
  rainy: {
    label: 'Rainy',
    description: 'Moderate rainfall, reduced visibility',
    riskModifier: 1.2,
  },
  fog: {
    label: 'Fog',
    description: 'Dense fog with very low visibility',
    riskModifier: 1.5,
  },
  severe: {
    label: 'Severe',
    description: 'Heavy rain, strong winds',
    riskModifier: 1.8,
  },
  flood: {
    label: 'Flood',
    description: 'Flooding conditions',
    riskModifier: 2.0,
  },
} as const;

/**
 * Traffic scenario configurations
 */
export const TRAFFIC_SCENARIOS = {
  light: {
    label: 'Light',
    description: 'Low traffic volume',
    riskModifier: 0.9,
  },
  moderate: {
    label: 'Moderate',
    description: 'Normal traffic conditions',
    riskModifier: 1.0,
  },
  heavy: {
    label: 'Heavy',
    description: 'High traffic volume',
    riskModifier: 1.3,
  },
  congested: {
    label: 'Congested',
    description: 'Heavy congestion, slow moving traffic',
    riskModifier: 1.6,
  },
} as const;

/**
 * Simulation status labels
 */
export const SIMULATION_STATUS_LABELS = {
  idle: 'Idle',
  initializing: 'Initializing',
  running: 'Running',
  paused: 'Paused',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
} as const;

/**
 * Simulation status colors
 */
export const SIMULATION_STATUS_COLORS = {
  idle: '#6b7280',      // Gray
  initializing: '#3b82f6', // Blue
  running: '#06b6d4',   // Cyan
  paused: '#f59e0b',    // Amber
  completed: '#10b981', // Green
  failed: '#ef4444',    // Red
  cancelled: '#a78bfa', // Violet
} as const;

/**
 * Default simulation configuration
 */
export const DEFAULT_SIMULATION_CONFIG = {
  duration: 24, // hours
  timeStep: 60, // minutes
  weatherScenario: 'rainy' as const,
  trafficScenario: 'moderate' as const,
  includeAccidents: true,
  riskFactorWeights: DEFAULT_RISK_FACTOR_WEIGHTS,
} as const;

/**
 * Polling configuration defaults
 */
export const DEFAULT_POLLING_CONFIG = {
  enabled: true,
  interval: 5000, // 5 seconds
  maxRetries: 5,
  backoffFactor: 2,
  stopOnCompletion: true,
} as const;

/**
 * Simulation API endpoints
 */
export const SIMULATION_ENDPOINTS = {
  BASE: '/simulations',
  CREATE: '/simulations/create',
  GET: (id: string) => `/simulations/${id}`,
  LIST: '/simulations/list',
  STATUS: (id: string) => `/simulations/${id}/status`,
  CANCEL: (id: string) => `/simulations/${id}/cancel`,
  HISTORY: '/simulations/history',
  RESULTS: (id: string) => `/simulations/${id}/results`,
} as const;

/**
 * Risk point generation limits
 */
export const RISK_POINT_LIMITS = {
  MIN_POINTS: 10,
  MAX_POINTS: 10000,
  DEFAULT_DENSITY: 100, // points per grid cell
} as const;

/**
 * Heatmap visualization settings
 */
export const HEATMAP_SETTINGS = {
  RADIUS: 50, // pixels
  BLUR: 15,   // pixels
  MAX_ZOOM: 18,
  MIN_ZOOM: 1,
  DEFAULT_OPACITY: 0.7,
} as const;

/**
 * Cache duration settings (in milliseconds)
 */
export const CACHE_DURATIONS = {
  RESULT: 5 * 60 * 1000,      // 5 minutes
  HISTORY: 10 * 60 * 1000,    // 10 minutes
  STATISTICS: 5 * 60 * 1000,  // 5 minutes
} as const;

/**
 * Simulation performance thresholds
 */
export const PERFORMANCE_THRESHOLDS = {
  WARNING_PROGRESS_SLOW: 10000, // ms (progress not updating)
  ERROR_TIMEOUT: 60000, // ms (operation timeout)
  MEMORY_LIMIT: 500 * 1024 * 1024, // 500MB
} as const;

/**
 * Risk factor descriptions
 */
export const RISK_FACTOR_DESCRIPTIONS: Record<string, string> = {
  weather: 'Weather conditions (precipitation, visibility, wind)',
  traffic: 'Traffic volume, congestion, and flow patterns',
  infrastructure: 'Road conditions, maintenance, closures',
  environmental: 'Terrain, geography, environmental hazards',
  accident: 'Historical accident patterns and frequencies',
  construction: 'Active construction zones and work areas',
} as const;

export default {
  RISK_LEVEL_COLORS,
  RISK_LEVEL_THRESHOLDS,
  DEFAULT_RISK_FACTOR_WEIGHTS,
  WEATHER_SCENARIOS,
  TRAFFIC_SCENARIOS,
  SIMULATION_STATUS_LABELS,
  SIMULATION_STATUS_COLORS,
  DEFAULT_SIMULATION_CONFIG,
  DEFAULT_POLLING_CONFIG,
  SIMULATION_ENDPOINTS,
  RISK_POINT_LIMITS,
  HEATMAP_SETTINGS,
  CACHE_DURATIONS,
  PERFORMANCE_THRESHOLDS,
  RISK_FACTOR_DESCRIPTIONS,
};
