/**
 * Risk Simulation Feature - API Module
 *
 * Handles all risk simulation API calls:
 * - Simulation creation and management
 * - Result fetching and polling
 * - History retrieval
 * - Real-time status updates
 */

import { API_BASE_URL, handleApiError } from '@/lib/api';
import type {
  RiskSimulationConfig,
  RiskSimulationResult,
  RiskSimulationHistory,
} from './types';
import { SIMULATION_ENDPOINTS, CACHE_DURATIONS } from './constants';

/**
 * Create a new risk simulation
 *
 * Initializes a simulation with provided configuration
 *
 * @example
 * ```ts
 * const result = await createSimulation({
 *   name: 'Morning Rush Hour Risk',
 *   bounds: { north: 40.8, south: 40.7, east: -73.9, west: -74.0 },
 *   duration: 2,
 *   timeStep: 10,
 *   weatherScenario: 'rainy',
 *   trafficScenario: 'heavy'
 * });
 * ```
 */
export async function createSimulation(config: Partial<RiskSimulationConfig>): Promise<RiskSimulationResult> {
  const response = await fetch(`${API_BASE_URL}${SIMULATION_ENDPOINTS.CREATE}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });

  if (!response.ok) {
    throw handleApiError(response);
  }

  const result = (await response.json()) as RiskSimulationResult;
  cacheResult(result);
  return result;
}

/**
 * Fetch simulation result by ID
 *
 * Retrieves current result state and data points
 *
 * @example
 * ```ts
 * const result = await fetchSimulationResult('sim-123');
 * console.log(`Progress: ${result.progress}%`);
 * ```
 */
export async function fetchSimulationResult(
  simulationId: string,
  options?: {
    /**
     * Cache timeout in ms
     */
    cacheTimeout?: number;

    /**
     * Include detailed risk points
     */
    includeDetails?: boolean;
  }
): Promise<RiskSimulationResult> {
  const cached = getCachedResult(simulationId);
  if (cached && (!options?.cacheTimeout || Date.now() - cached.timestamp < options.cacheTimeout)) {
    return cached.data;
  }

  const params = new URLSearchParams();
  if (options?.includeDetails) {
    params.append('details', 'true');
  }

  const response = await fetch(
    `${API_BASE_URL}${SIMULATION_ENDPOINTS.GET(simulationId)}${params.toString() ? `?${params}` : ''}`
  );

  if (!response.ok) {
    throw handleApiError(response);
  }

  const result = (await response.json()) as RiskSimulationResult;
  cacheResult(result);
  return result;
}

/**
 * Get simulation status (lightweight endpoint)
 *
 * Returns only status and progress without full result data
 *
 * @example
 * ```ts
 * const status = await getSimulationStatus('sim-123');
 * if (status.status === 'completed') {
 *   // Fetch full result
 * }
 * ```
 */
export async function getSimulationStatus(simulationId: string): Promise<{
  status: string;
  progress: number;
  updatedAt: string;
  error?: string;
}> {
  const response = await fetch(
    `${API_BASE_URL}${SIMULATION_ENDPOINTS.STATUS(simulationId)}`
  );

  if (!response.ok) {
    throw handleApiError(response);
  }

  return response.json() as Promise<{ status: string; progress: number; updatedAt: string; error?: string }>;
}

/**
 * Fetch simulation history
 *
 * Returns list of past simulations
 *
 * @example
 * ```ts
 * const history = await fetchSimulationHistory({
 *   limit: 20,
 *   offset: 0,
 *   sortBy: 'timestamp',
 *   sortOrder: 'desc'
 * });
 * ```
 */
export async function fetchSimulationHistory(options?: {
  /**
   * Number of results to return
   */
  limit?: number;

  /**
   * Offset for pagination
   */
  offset?: number;

  /**
   * Sort field
   */
  sortBy?: 'timestamp' | 'name' | 'duration';

  /**
   * Sort direction
   */
  sortOrder?: 'asc' | 'desc';

  /**
   * Filter by status
   */
  status?: string;

  /**
   * Filter by tags
   */
  tags?: string[];
}): Promise<RiskSimulationHistory[]> {
  const params = new URLSearchParams();
  if (options?.limit) params.append('limit', String(options.limit));
  if (options?.offset) params.append('offset', String(options.offset));
  if (options?.sortBy) params.append('sortBy', options.sortBy);
  if (options?.sortOrder) params.append('sortOrder', options.sortOrder);
  if (options?.status) params.append('status', options.status);
  if (options?.tags?.length) params.append('tags', options.tags.join(','));

  const response = await fetch(
    `${API_BASE_URL}${SIMULATION_ENDPOINTS.HISTORY}${params.toString() ? `?${params}` : ''}`
  );

  if (!response.ok) {
    throw handleApiError(response);
  }

  const history = (await response.json()) as RiskSimulationHistory[];
  cacheHistory(history);
  return history;
}

/**
 * Cancel a running simulation
 *
 * Stops simulation and returns final result
 *
 * @example
 * ```ts
 * const result = await cancelSimulation('sim-123');
 * console.log(`Cancelled. Generated ${result.riskPoints.length} points`);
 * ```
 */
export async function cancelSimulation(simulationId: string): Promise<RiskSimulationResult> {
  const response = await fetch(
    `${API_BASE_URL}${SIMULATION_ENDPOINTS.CANCEL(simulationId)}`,
    { method: 'POST' }
  );

  if (!response.ok) {
    throw handleApiError(response);
  }

  return response.json() as Promise<RiskSimulationResult>;
}

/**
 * List all simulations
 *
 * @example
 * ```ts
 * const simulations = await listSimulations();
 * ```
 */
export async function listSimulations(): Promise<RiskSimulationResult[]> {
  const response = await fetch(`${API_BASE_URL}${SIMULATION_ENDPOINTS.LIST}`);

  if (!response.ok) {
    throw handleApiError(response);
  }

  return response.json() as Promise<RiskSimulationResult[]>;
}

/**
 * Subscribe to simulation updates via WebSocket
 *
 * Real-time status and progress updates
 *
 * @example
 * ```ts
 * const unsubscribe = subscribeToSimulation('sim-123', {
 *   onUpdate: (result) => updateUI(result),
 *   onProgress: (progress) => updateProgressBar(progress),
 *   onComplete: (result) => showResults(result),
 *   onError: (error) => showError(error)
 * });
 *
 * // Later...
 * unsubscribe();
 * ```
 */
export function subscribeToSimulation(
  simulationId: string,
  options: {
    /**
     * Update callback
     */
    onUpdate?: (result: RiskSimulationResult) => void;

    /**
     * Progress callback
     */
    onProgress?: (progress: number) => void;

    /**
     * Completion callback
     */
    onComplete?: (result: RiskSimulationResult) => void;

    /**
     * Error callback
     */
    onError?: (error: Error) => void;

    /**
     * Connect callback
     */
    onConnect?: () => void;

    /**
     * Disconnect callback
     */
    onDisconnect?: () => void;
  }
): () => void {
  const wsProtocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss' : 'ws';
  const wsUrl = new URL(
    `/simulations/${simulationId}/stream`,
    `${wsProtocol}://${API_BASE_URL.replace(/^https?:\/\//, '')}`
  );

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

          if (data.type === 'update') {
            const result = data.payload as RiskSimulationResult;
            cacheResult(result);
            options.onUpdate?.(result);
          } else if (data.type === 'progress') {
            options.onProgress?.(data.payload);
          } else if (data.type === 'completed') {
            const result = data.payload as RiskSimulationResult;
            cacheResult(result);
            options.onComplete?.(result);
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
          // Attempt reconnect
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
 * Cache simulation result
 */
function cacheResult(result: RiskSimulationResult): void {
  try {
    localStorage.setItem(
      `risk_result_${result.id}`,
      JSON.stringify({
        data: result,
        timestamp: Date.now(),
      })
    );
  } catch (error) {
    console.warn('[Risk API] Cache write failed:', error);
  }
}

/**
 * Get cached simulation result
 */
function getCachedResult(
  simulationId: string
): { data: RiskSimulationResult; timestamp: number } | null {
  try {
    const cached = localStorage.getItem(`risk_result_${simulationId}`);
    if (!cached) return null;

    return JSON.parse(cached) as { data: RiskSimulationResult; timestamp: number };
  } catch {
    return null;
  }
}

/**
 * Cache simulation history
 */
function cacheHistory(history: RiskSimulationHistory[]): void {
  try {
    localStorage.setItem(
      'risk_history_cache',
      JSON.stringify({
        data: history,
        timestamp: Date.now(),
      })
    );
  } catch (error) {
    console.warn('[Risk API] History cache write failed:', error);
  }
}

/**
 * Get cached history
 */
function getCachedHistory(): RiskSimulationHistory[] | null {
  try {
    const cached = localStorage.getItem('risk_history_cache');
    if (!cached) return null;

    const parsed = JSON.parse(cached) as {
      data: RiskSimulationHistory[];
      timestamp: number;
    };

    if (Date.now() - parsed.timestamp > CACHE_DURATIONS.HISTORY) {
      return null;
    }

    return parsed.data;
  } catch {
    return null;
  }
}

export default {
  createSimulation,
  fetchSimulationResult,
  getSimulationStatus,
  fetchSimulationHistory,
  cancelSimulation,
  listSimulations,
  subscribeToSimulation,
};
