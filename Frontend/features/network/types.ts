/**
 * Network Types
 * Type definitions for geospatial network domain
 * 
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 5.1.3: Network Domain)
 */

/**
 * Map bounds for viewport queries
 */
export interface MapBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

/**
 * Geographic coordinates (longitude, latitude)
 */
export interface LatLng {
  lat: number;
  lng: number;
}

/**
 * Road segment with risk information
 */
export interface RouteSegment {
  /** Segment ID */
  id: string;

  /** Encoded polyline (compressed coordinates) */
  encodedPolyline: string;

  /** Risk score (0-100) */
  risk_score: number;

  /** Risk category */
  risk_category: 'low' | 'medium' | 'high' | 'critical';

  /** Start point */
  start: LatLng;

  /** End point */
  end: LatLng;

  /** Distance in kilometers */
  distance_km: number;

  /** Estimated travel time in seconds */
  duration_seconds: number;

  /** Weather conditions on this segment */
  weather_status?: 'clear' | 'rainy' | 'heavy_rain' | 'flooding';

  /** Traffic status */
  traffic_status?: 'free_flow' | 'moderate' | 'congested' | 'blocked';

  /** Additional metadata */
  metadata?: Record<string, any>;
}

/**
 * Complete route with multiple segments
 */
export interface RoutePolyline {
  /** Route ID (e.g., 'NH-06', 'route-1') */
  id: string;

  /** Route name (e.g., 'Delhi - Jaipur Corridor') */
  name: string;

  /** Route segments with encoded polylines */
  segments: RouteSegment[];

  /** Overall route risk score (average of segments) */
  risk_score: number;

  /** Total distance in kilometers */
  total_distance_km: number;

  /** Total estimated travel time in seconds */
  total_duration_seconds: number;

  /** Data source ('primary' or 'internal_postgis' for offline) */
  source?: 'primary' | 'internal_postgis' | 'cached';

  /** Last updated timestamp */
  updated_at?: string;

  /** Additional route metadata */
  metadata?: Record<string, any>;
}

/**
 * Road network containing multiple routes
 */
export interface RoadNetwork {
  /** Array of routes in network */
  routes: RoutePolyline[];

  /** Map bounds for this network */
  bounds: MapBounds;

  /** Last updated timestamp */
  lastUpdated: string;

  /** Data source */
  source?: 'primary' | 'internal_postgis' | 'cached';

  /** Network statistics */
  stats?: {
    totalRoutes: number;
    averageRiskScore: number;
    criticalRoutes: number;
    affectedByWeather: number;
  };
}

/**
 * Map interaction state
 */
export interface MapInteractionState {
  /** Current zoom level (0-21) */
  zoom: number;

  /** Map center coordinates */
  center: LatLng;

  /** Current map bounds */
  bounds: MapBounds;

  /** Selected route ID (if any) */
  selectedRouteId?: string;

  /** Whether to show weather layer */
  showWeatherLayer: boolean;

  /** Whether to show route layer */
  showRouteLayer: boolean;

  /** Whether to show traffic layer */
  showTrafficLayer: boolean;
}

/**
 * Route interaction event
 */
export interface RouteInteractionEvent {
  /** Event type */
  type: 'select' | 'deselect' | 'hover' | 'click' | 'detail';

  /** Route ID */
  routeId?: string;

  /** Segment ID (if segment-specific) */
  segmentId?: string;

  /** Coordinates where interaction occurred */
  coordinates?: LatLng;

  /** Timestamp */
  timestamp: number;
}

/**
 * Offline route backup info
 */
export interface OfflineBackupInfo {
  /** Whether offline backup is available */
  available: boolean;

  /** Last sync timestamp */
  lastSynced?: string;

  /** Number of routes cached */
  routesCached: number;

  /** Total cached data size in MB */
  cacheSizeMB: number;

  /** Expiry status of cached data */
  isExpired: boolean;
}

/**
 * Node (intersection/waypoint) information
 */
export interface RoadNode {
  /** Node ID */
  id: string;

  /** Node coordinates */
  coordinates: LatLng;

  /** Node type (intersection, waypoint, etc.) */
  type: 'intersection' | 'waypoint' | 'landmark' | 'service_station';

  /** Node name/address */
  name: string;

  /** Connected routes */
  connectedRoutes: string[];

  /** Risk at this location */
  risk_score?: number;

  /** Metadata */
  metadata?: Record<string, any>;
}

/**
 * Polyline decoder result
 */
export interface DecodedPolyline {
  /** Array of [latitude, longitude] coordinates */
  coordinates: Array<[number, number]>;

  /** Total distance in kilometers */
  distanceKm: number;

  /** Bounding box of polyline */
  bounds: MapBounds;
}

/**
 * Route list item (simplified for sidebar/list view)
 */
export interface RouteListItem {
  id: string;
  name: string;
  riskScore: number;
  distance: number;
  selectedCount?: number; // For analytics
}

/**
 * Network layer options
 */
export interface NetworkLayerOptions {
  /** Show risk colors (gradient based on risk_score) */
  showRiskColors: boolean;

  /** Risk color mapping */
  riskColors?: {
    low: string; // green
    medium: string; // yellow
    high: string; // orange
    critical: string; // red
  };

  /** Show traffic information */
  showTraffic: boolean;

  /** Show weather conditions */
  showWeather: boolean;

  /** Polyline opacity (0-1) */
  polylineOpacity: number;

  /** Polyline weight (pixels) */
  polylineWeight: number;

  /** Highlight color for selected route */
  highlightColor: string;
}
