/**
 * Network API
 * Handles all geospatial network API calls
 * 
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 5.1.3: Network Domain)
 */

import type { RoadNetwork, RoutePolyline, RouteSegment } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * ============================================
 * Road Network Endpoints
 * ============================================
 */

/**
 * GET /network/road-graph
 * Fetch road network for specified bounds
 * 
 * @param bounds - Map bounds (north, south, east, west)
 * @returns RoadNetwork with routes and metadata
 */
export async function getRoadNetwork(bounds?: {
  north: number;
  south: number;
  east: number;
  west: number;
}): Promise<RoadNetwork> {
  const params = new URLSearchParams();
  if (bounds) {
    params.append('north', String(bounds.north));
    params.append('south', String(bounds.south));
    params.append('east', String(bounds.east));
    params.append('west', String(bounds.west));
  }

  const response = await fetch(
    `${API_BASE_URL}/network/road-graph?${params}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch road network: ${response.status}`);
  }

  return response.json();
}

/**
 * GET /network/routes/{id}
 * Fetch detailed route information with polylines and segments
 * 
 * @param routeId - Route ID (e.g., 'route-1', 'NH-06')
 * @returns RoutePolyline with encoded polylines and risk scores
 */
export async function getRouteDetails(routeId: string): Promise<RoutePolyline | null> {
  const response = await fetch(
    `${API_BASE_URL}/network/routes/${routeId}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    if (response.status === 404) {
      return null;
    }
    throw new Error(`Failed to fetch route details: ${response.status}`);
  }

  return response.json();
}

/**
 * POST /network/routes/search
 * Search routes by name or ID
 * 
 * @param query - Search query (name or ID pattern)
 * @returns Array of matching routes
 */
export async function searchRoutes(query: string): Promise<RoutePolyline[]> {
  const response = await fetch(`${API_BASE_URL}/network/routes/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    throw new Error(`Route search failed: ${response.status}`);
  }

  return response.json();
}

/**
 * ============================================
 * Risk Data Endpoints
 * ============================================
 */

/**
 * GET /network/routes/{id}/risk-scores
 * Fetch risk scores for specific route segments
 * 
 * @param routeId - Route ID
 * @returns Array of segments with risk scores
 */
export async function getRouteRiskScores(routeId: string): Promise<RouteSegment[]> {
  const response = await fetch(
    `${API_BASE_URL}/network/routes/${routeId}/risk-scores`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch risk scores: ${response.status}`);
  }

  return response.json();
}

/**
 * ============================================
 * Offline Backup Endpoints
 * ============================================
 */

/**
 * GET /network/routes/{id}/offline-backup
 * Fetch offline backup route (from internal PostGIS)
 * 
 * Used when primary API is unavailable
 * 
 * @param routeId - Route ID
 * @returns Offline backup route data
 */
export async function getOfflineBackupRoute(routeId: string): Promise<RoutePolyline | null> {
  const response = await fetch(
    `${API_BASE_URL}/network/routes/${routeId}/offline-backup`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    if (response.status === 404) {
      return null;
    }
    throw new Error(`Offline backup fetch failed: ${response.status}`);
  }

  const data = await response.json();
  
  // Mark as offline backup
  return {
    ...data,
    source: 'internal_postgis',
  };
}

/**
 * ============================================
 * Real-Time Updates Endpoints
 * ============================================
 */

/**
 * GET /network/live/traffic
 * Fetch real-time traffic data (WebSocket fallback via polling)
 * 
 * @param bounds - Map bounds for traffic data
 * @returns Traffic status for routes
 */
export async function getTrafficStatus(bounds?: {
  north: number;
  south: number;
  east: number;
  west: number;
}): Promise<any> {
  const params = new URLSearchParams();
  if (bounds) {
    params.append('north', String(bounds.north));
    params.append('south', String(bounds.south));
    params.append('east', String(bounds.east));
    params.append('west', String(bounds.west));
  }

  const response = await fetch(
    `${API_BASE_URL}/network/live/traffic?${params}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Traffic data fetch failed: ${response.status}`);
  }

  return response.json();
}

export const NetworkAPI = {
  getRoadNetwork,
  getRouteDetails,
  searchRoutes,
  getRouteRiskScores,
  getOfflineBackupRoute,
  getTrafficStatus,
};
