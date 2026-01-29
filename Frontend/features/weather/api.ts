/**
 * Weather Feature - API Module
 *
 * Handles all weather-related API calls:
 * - Weather grid data fetching
 * - Alert retrieval and management
 * - Rainfall heatmap generation
 * - Forecast data
 * - Real-time polling support
 */

import { API_BASE_URL, handleApiError } from '@/lib/api';
import type {
  WeatherGrid,
  WeatherAlert,
  RainfallHeatmapData,
  WeatherForecast,
  WeatherGridCell,
} from './types';

/**
 * Fetch weather grid data
 *
 * Retrieves current weather conditions for all grid cells
 * in the specified geographic bounds
 *
 * @example
 * ```ts
 * const grid = await fetchWeatherGrid({
 *   bounds: {
 *     north: 40.8,
 *     south: 40.7,
 *     east: -73.9,
 *     west: -74.0
 *   }
 * });
 * ```
 */
export async function fetchWeatherGrid(options?: {
  /**
   * Geographic bounds for grid
   */
  bounds?: {
    north: number;
    south: number;
    east: number;
    west: number;
  };

  /**
   * Grid resolution override (degrees)
   */
  resolution?: number;

  /**
   * Include forecast data
   */
  includeForecast?: boolean;

  /**
   * Cache timeout in ms (default: 5 min)
   */
  cacheTimeout?: number;
}): Promise<WeatherGrid> {
  const params = new URLSearchParams();

  if (options?.bounds) {
    params.append('north', String(options.bounds.north));
    params.append('south', String(options.bounds.south));
    params.append('east', String(options.bounds.east));
    params.append('west', String(options.bounds.west));
  }

  if (options?.resolution) {
    params.append('resolution', String(options.resolution));
  }

  if (options?.includeForecast) {
    params.append('includeForecast', 'true');
  }

  const response = await fetch(
    `${API_BASE_URL}/weather/grid${params.toString() ? `?${params}` : ''}`
  );

  if (!response.ok) {
    throw handleApiError(response);
  }

  return response.json() as Promise<WeatherGrid>;
}

/**
 * Fetch active weather alerts
 *
 * Returns all active alerts affecting the specified area
 *
 * @example
 * ```ts
 * const alerts = await fetchWeatherAlerts({
 *   area: { north: 40.8, south: 40.7, east: -73.9, west: -74.0 }
 * });
 * ```
 */
export async function fetchWeatherAlerts(options?: {
  /**
   * Geographic area for alerts
   */
  area?: {
    north: number;
    south: number;
    east: number;
    west: number;
  };

  /**
   * Filter by alert type
   */
  type?: 'warning' | 'alert' | 'advisory' | 'watch';

  /**
   * Minimum severity level (1-5)
   */
  minSeverity?: number;

  /**
   * Only active alerts
   */
  onlyActive?: boolean;
}): Promise<WeatherAlert[]> {
  const params = new URLSearchParams();

  if (options?.area) {
    params.append('north', String(options.area.north));
    params.append('south', String(options.area.south));
    params.append('east', String(options.area.east));
    params.append('west', String(options.area.west));
  }

  if (options?.type) {
    params.append('type', options.type);
  }

  if (options?.minSeverity) {
    params.append('minSeverity', String(options.minSeverity));
  }

  if (options?.onlyActive !== false) {
    params.append('onlyActive', 'true');
  }

  const response = await fetch(
    `${API_BASE_URL}/weather/alerts${params.toString() ? `?${params}` : ''}`
  );

  if (!response.ok) {
    throw handleApiError(response);
  }

  return response.json() as Promise<WeatherAlert[]>;
}

/**
 * Fetch rainfall heatmap data
 *
 * Returns aggregated precipitation data for visualization
 *
 * @example
 * ```ts
 * const heatmap = await fetchRainfallHeatmap({
 *   bounds: { north: 40.8, south: 40.7, east: -73.9, west: -74.0 }
 * });
 * ```
 */
export async function fetchRainfallHeatmap(options?: {
  /**
   * Geographic bounds
   */
  bounds?: {
    north: number;
    south: number;
    east: number;
    west: number;
  };

  /**
   * Forecast hours (0 = current)
   */
  forecastHour?: number;

  /**
   * Data resolution (affects point density)
   */
  resolution?: 'low' | 'medium' | 'high';
}): Promise<RainfallHeatmapData> {
  const params = new URLSearchParams();

  if (options?.bounds) {
    params.append('north', String(options.bounds.north));
    params.append('south', String(options.bounds.south));
    params.append('east', String(options.bounds.east));
    params.append('west', String(options.bounds.west));
  }

  if (options?.forecastHour !== undefined) {
    params.append('forecastHour', String(options.forecastHour));
  }

  if (options?.resolution) {
    params.append('resolution', options.resolution);
  }

  const response = await fetch(
    `${API_BASE_URL}/weather/rainfall-heatmap${params.toString() ? `?${params}` : ''}`
  );

  if (!response.ok) {
    throw handleApiError(response);
  }

  return response.json() as Promise<RainfallHeatmapData>;
}

/**
 * Fetch weather forecast for a specific location
 *
 * Returns time-series weather predictions
 *
 * @example
 * ```ts
 * const forecast = await fetchWeatherForecast({
 *   latitude: 40.7128,
 *   longitude: -74.0060,
 *   hours: 24
 * });
 * ```
 */
export async function fetchWeatherForecast(options: {
  /**
   * Target latitude
   */
  latitude: number;

  /**
   * Target longitude
   */
  longitude: number;

  /**
   * Forecast hours (1-168)
   */
  hours?: number;
}): Promise<WeatherForecast> {
  const params = new URLSearchParams({
    latitude: String(options.latitude),
    longitude: String(options.longitude),
    hours: String(options.hours ?? 24),
  });

  const response = await fetch(
    `${API_BASE_URL}/weather/forecast?${params}`
  );

  if (!response.ok) {
    throw handleApiError(response);
  }

  return response.json() as Promise<WeatherForecast>;
}

/**
 * Get a specific weather grid cell details
 *
 * @example
 * ```ts
 * const cell = await fetchWeatherCell('grid-cell-123');
 * ```
 */
export async function fetchWeatherCell(cellId: string): Promise<WeatherGridCell> {
  const response = await fetch(
    `${API_BASE_URL}/weather/grid/${cellId}`
  );

  if (!response.ok) {
    throw handleApiError(response);
  }

  return response.json() as Promise<WeatherGridCell>;
}

/**
 * Subscribe to real-time weather updates via WebSocket
 *
 * @example
 * ```ts
 * const unsubscribe = subscribeToWeatherUpdates({
 *   bounds: { north: 40.8, south: 40.7, east: -73.9, west: -74.0 },
 *   onUpdate: (grid) => console.log('New grid:', grid),
 *   onAlert: (alert) => console.log('New alert:', alert),
 *   onError: (error) => console.error('WS error:', error)
 * });
 *
 * // Later...
 * unsubscribe();
 * ```
 */
export function subscribeToWeatherUpdates(options: {
  /**
   * Geographic bounds
   */
  bounds?: {
    north: number;
    south: number;
    east: number;
    west: number;
  };

  /**
   * Callback for grid updates
   */
  onUpdate: (grid: WeatherGrid) => void;

  /**
   * Callback for new alerts
   */
  onAlert?: (alert: WeatherAlert) => void;

  /**
   * Callback for errors
   */
  onError?: (error: Error) => void;

  /**
   * Callback on connection
   */
  onConnect?: () => void;

  /**
   * Callback on disconnect
   */
  onDisconnect?: () => void;
}): () => void {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const wsUrl = new URL(
    '/weather/stream',
    `${wsProtocol}://${API_BASE_URL.replace(/^https?:\/\//, '')}`
  );

  if (options.bounds) {
    wsUrl.searchParams.append('north', String(options.bounds.north));
    wsUrl.searchParams.append('south', String(options.bounds.south));
    wsUrl.searchParams.append('east', String(options.bounds.east));
    wsUrl.searchParams.append('west', String(options.bounds.west));
  }

  let ws: WebSocket | null = null;
  let reconnectTimer: NodeJS.Timeout | null = null;
  let isClosed = false;

  const connect = () => {
    try {
      ws = new WebSocket(wsUrl.toString());

      ws.onopen = () => {
        options.onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'grid') {
            options.onUpdate(data.payload);
          } else if (data.type === 'alert') {
            options.onAlert?.(data.payload);
          }
        } catch (error) {
          options.onError?.(
            error instanceof Error
              ? error
              : new Error('Failed to parse WebSocket message')
          );
        }
      };

      ws.onerror = (event) => {
        options.onError?.(
          new Error(
            `WebSocket error: ${event instanceof Event ? event.type : 'unknown'}`
          )
        );
      };

      ws.onclose = () => {
        if (!isClosed) {
          options.onDisconnect?.();
          // Attempt reconnect with backoff
          reconnectTimer = setTimeout(connect, 3000);
        }
      };
    } catch (error) {
      options.onError?.(
        error instanceof Error ? error : new Error('WebSocket connection failed')
      );
    }
  };

  connect();

  return () => {
    isClosed = true;
    if (reconnectTimer) clearTimeout(reconnectTimer);
    if (ws) ws.close();
  };
}

/**
 * Cache weather grid data
 *
 * Save grid to local storage for offline access
 */
export function cacheWeatherGrid(grid: WeatherGrid): void {
  try {
    localStorage.setItem(
      'weather_grid_cache',
      JSON.stringify({
        data: grid,
        timestamp: Date.now(),
      })
    );
  } catch (error) {
    console.warn('[Weather API] Cache write failed:', error);
  }
}

/**
 * Get cached weather grid
 *
 * @param maxAge Maximum age in milliseconds (default: 10 min)
 */
export function getCachedWeatherGrid(maxAge = 10 * 60 * 1000): WeatherGrid | null {
  try {
    const cached = localStorage.getItem('weather_grid_cache');
    if (!cached) return null;

    const parsed = JSON.parse(cached) as {
      data: WeatherGrid;
      timestamp: number;
    };

    if (Date.now() - parsed.timestamp > maxAge) {
      return null;
    }

    return parsed.data;
  } catch {
    return null;
  }
}

export default {
  fetchWeatherGrid,
  fetchWeatherAlerts,
  fetchRainfallHeatmap,
  fetchWeatherForecast,
  fetchWeatherCell,
  subscribeToWeatherUpdates,
  cacheWeatherGrid,
  getCachedWeatherGrid,
};
