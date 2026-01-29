'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { fetchWeatherGrid, getCachedWeatherGrid } from '../api';
import type { WeatherGrid, WeatherPollingConfig } from '../types';

/**
 * useWeatherPolling Hook
 *
 * Manages continuous polling of weather data with intelligent backoff and fallback
 *
 * **Features**:
 * - Configurable polling interval
 * - Exponential backoff on errors
 * - Automatic fallback to cached data
 * - Connection state tracking
 * - Manual pause/resume
 * - Error recovery strategies
 *
 * **Polling Strategies**:
 * 1. **Normal**: Poll at configured interval
 * 2. **Degraded**: If errors occur, increase interval and use cache
 * 3. **Offline**: Use cached data, attempt reconnect periodically
 * 4. **Manual**: User controls when to poll
 *
 * **Usage**:
 * ```tsx
 * const {
 *   grid,
 *   isPolling,
 *   isConnected,
 *   error,
 *   pause,
 *   resume,
 *   poll
 * } = useWeatherPolling({
 *   bounds: { north: 40.8, south: 40.7, east: -73.9, west: -74.0 },
 *   interval: 30000, // 30 seconds
 *   maxRetries: 3,
 *   onConnected: () => showToast('Connected'),
 *   onDisconnected: () => showToast('Disconnected')
 * });
 *
 * return (
 *   <>
 *     <GridVisualization grid={grid} />
 *     <StatusBadge isConnected={isConnected} />
 *     <Button onClick={isPolling ? pause : resume}>
 *       {isPolling ? 'Pause' : 'Resume'}
 *     </Button>
 *   </>
 * );
 * ```
 *
 * **Connection States**:
 * - `isConnected=true, isPolling=true`: Normal operation
 * - `isConnected=false, isPolling=true`: Degraded (using backoff)
 * - `isConnected=false, isPolling=false`: Paused or offline
 * - `error !== null`: Last poll failed
 *
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 6.1: Polling Strategy)
 */
export function useWeatherPolling(options?: {
  /**
   * Geographic bounds for polling
   */
  bounds?: {
    north: number;
    south: number;
    east: number;
    west: number;
  };

  /**
   * Poll interval in milliseconds (default: 30000)
   */
  interval?: number;

  /**
   * Maximum retry attempts (default: 3)
   */
  maxRetries?: number;

  /**
   * Backoff factor (default: 2)
   */
  backoffFactor?: number;

  /**
   * Start polling immediately (default: true)
   */
  autoStart?: boolean;

  /**
   * Include forecast data
   */
  includeForecast?: boolean;

  /**
   * Callback when connection established
   */
  onConnected?: () => void;

  /**
   * Callback when connection lost
   */
  onDisconnected?: () => void;

  /**
   * Callback on poll error
   */
  onError?: (error: Error, retryCount: number) => void;

  /**
   * Callback on successful poll
   */
  onSuccess?: (grid: WeatherGrid) => void;
}) {
  const {
    bounds,
    interval = 30000,
    maxRetries = 3,
    backoffFactor = 2,
    autoStart = true,
    includeForecast = false,
    onConnected,
    onDisconnected,
    onError: onErrorCallback,
    onSuccess,
  } = options || {};

  const [grid, setGrid] = useState<WeatherGrid | null>(null);
  const [isPolling, setIsPolling] = useState(autoStart);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isConnectedRef = useRef(isConnected);
  const retryCountRef = useRef(retryCount);

  // Keep refs in sync
  useEffect(() => {
    isConnectedRef.current = isConnected;
  }, [isConnected]);

  useEffect(() => {
    retryCountRef.current = retryCount;
  }, [retryCount]);

  const calculateInterval = useCallback(() => {
    // Exponential backoff: base * (factor ^ retryCount)
    return interval * Math.pow(backoffFactor, Math.min(retryCount, 3));
  }, [interval, backoffFactor, retryCount]);

  const poll = useCallback(async () => {
    try {
      const newGrid = await fetchWeatherGrid({
        bounds,
        includeForecast,
        cacheTimeout: 10 * 60 * 1000,
      });

      setGrid(newGrid);
      setError(null);
      setRetryCount(0);

      // Update connection status if was disconnected
      if (!isConnectedRef.current) {
        setIsConnected(true);
        onConnected?.();
      }

      onSuccess?.(newGrid);
    } catch (err) {
      const error =
        err instanceof Error ? err : new Error('Weather poll failed');
      setError(error);

      const nextRetryCount = retryCountRef.current + 1;
      setRetryCount(nextRetryCount);

      // Try fallback to cache
      const cached = getCachedWeatherGrid();
      if (cached) {
        setGrid(cached);
        console.warn('[useWeatherPolling] Using cached data:', error.message);
      }

      if (nextRetryCount >= maxRetries) {
        // Max retries exceeded
        if (isConnectedRef.current) {
          setIsConnected(false);
          onDisconnected?.();
        }
      }

      onErrorCallback?.(error, nextRetryCount);
    }
  }, [bounds, includeForecast, maxRetries, onConnected, onDisconnected, onErrorCallback, onSuccess]);

  // Main polling loop
  useEffect(() => {
    if (!isPolling) {
      if (pollingIntervalRef.current) {
        clearTimeout(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      return;
    }

    // Poll immediately
    poll();

    // Set up polling
    const scheduleNextPoll = () => {
      const nextInterval = calculateInterval();
      pollingIntervalRef.current = setTimeout(() => {
        poll();
        scheduleNextPoll();
      }, nextInterval);
    };

    scheduleNextPoll();

    return () => {
      if (pollingIntervalRef.current) {
        clearTimeout(pollingIntervalRef.current);
      }
    };
  }, [isPolling, poll, calculateInterval]);

  const pause = useCallback(() => {
    setIsPolling(false);
  }, []);

  const resume = useCallback(() => {
    setIsPolling(true);
    setRetryCount(0); // Reset retries on resume
  }, []);

  const manualPoll = useCallback(async () => {
    await poll();
  }, [poll]);

  return {
    /**
     * Current weather grid
     */
    grid,

    /**
     * Is polling active
     */
    isPolling,

    /**
     * Is connected (last poll succeeded)
     */
    isConnected,

    /**
     * Last error
     */
    error,

    /**
     * Current retry attempt
     */
    retryCount,

    /**
     * Current polling interval (adjusted for backoff)
     */
    currentInterval: calculateInterval(),

    /**
     * Pause polling
     */
    pause,

    /**
     * Resume polling
     */
    resume,

    /**
     * Manual poll trigger
     */
    poll: manualPoll,

    /**
     * Reset connection state
     */
    reset: () => {
      setError(null);
      setRetryCount(0);
      setIsConnected(false);
    },
  };
}

export default useWeatherPolling;
