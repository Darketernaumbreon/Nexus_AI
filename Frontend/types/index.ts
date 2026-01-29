// NEXUS AI - Global Type Definitions

// ============================================
// API Error Types
// ============================================
export interface ApiError {
  status: number;
  message: string;
  detail?: string;
}

// ============================================
// Authentication Types
// ============================================
export interface User {
  id: string;
  username: string;
  email: string;
  fullName?: string;
  role: "admin" | "operator" | "viewer";
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

// ============================================
// Network / Geospatial Types
// ============================================
export interface Coordinates {
  lat: number;
  lng: number;
}

export interface Bounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

export interface RouteSegment {
  id: string;
  encodedPolyline: string;
  risk_score: number;
  name: string;
  length_km: number;
  surface_type?: string;
}

export interface RoutePolyline {
  id: string;
  name: string;
  segments: RouteSegment[];
  total_length_km: number;
  average_risk_score: number;
  coordinates?: number[][]; // [lon, lat] arrays
  source: "osrm" | "internal_postgis";
}

export interface RoadNetwork {
  routes: RoutePolyline[];
  lastUpdated: string;
  bounds: Bounds;
}

export interface NodeDetails {
  id: string;
  name: string;
  type: "junction" | "checkpoint" | "village";
  coordinates: Coordinates;
  risk_score: number;
  metadata?: Record<string, unknown>;
}

// ============================================
// Weather Types
// ============================================
export interface WeatherCell {
  id: string;
  bounds: Bounds;
  rainfall_mm: number;
  temperature_c: number;
  humidity_percent: number;
  timestamp: string;
}

export interface WeatherAlert {
  id: string;
  type: "flood" | "storm" | "heavy_rain" | "drought";
  severity: "low" | "medium" | "high" | "critical";
  message: string;
  affected_regions: string[];
  valid_from: string;
  valid_until: string;
}

export interface WeatherGrid {
  cells: WeatherCell[];
  alerts: WeatherAlert[];
  lastUpdated: string;
}

// ============================================
// Risk / Simulation Types
// ============================================
export type JobStatus =
  | "QUEUED"
  | "PROCESSING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export interface SimulationRequest {
  region_id: string;
  model_version?: string;
}

export interface SimulationJob {
  job_id: string;
  region_id: string;
  status: JobStatus;
  progress: number;
  eta_seconds?: number;
  created_at: string;
  updated_at: string;
}

export interface SimulationResult {
  job_id: string;
  region_id: string;
  status: JobStatus;
  progress: number;
  eta_seconds?: number;
  results?: {
    risk_assessment: {
      overall_score: number;
      confidence: number;
      factors: Array<{
        name: string;
        contribution: number;
        value: number;
      }>;
    };
    recommendations: Array<{
      priority: "high" | "medium" | "low";
      action: string;
      impact: string;
    }>;
    affected_routes: Array<{
      route_id: string;
      name: string;
      risk_change: number;
    }>;
  };
  error?: string;
}

// ============================================
// System Health Types
// ============================================
export interface HealthStatus {
  isAlive: boolean;
  isReady: boolean;
  lastCheck: Date;
}

// ============================================
// UI State Types
// ============================================
export interface ToastData {
  id: string;
  type: "success" | "error" | "warning" | "info";
  title: string;
  description?: string;
  duration?: number;
}

// ============================================
// Navigation Types
// ============================================
export interface NavItem {
  label: string;
  href: string;
  icon: string;
  badge?: string | number;
}

// ============================================
// Region Data
// ============================================
export interface Region {
  id: string;
  name: string;
  code: string;
  bounds: Bounds;
}

export const REGIONS: Region[] = [
  {
    id: "NH-06",
    name: "National Highway 6",
    code: "NH-06",
    bounds: { north: 23.5, south: 22.5, east: 88.5, west: 87.5 },
  },
  {
    id: "NH-44",
    name: "National Highway 44 (Expressway)",
    code: "NH-44",
    bounds: { north: 28.5, south: 12.5, east: 78.5, west: 77.0 },
  },
  {
    id: "NH-48",
    name: "National Highway 48",
    code: "NH-48",
    bounds: { north: 28.7, south: 19.0, east: 77.5, west: 72.8 },
  },
  {
    id: "NH-27",
    name: "National Highway 27",
    code: "NH-27",
    bounds: { north: 27.0, south: 22.0, east: 94.0, west: 69.5 },
  },
];
