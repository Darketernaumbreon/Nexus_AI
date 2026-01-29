'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { fetchSimulationResult } from '../api';
import type { RiskSimulationResult } from '../types';
import { CACHE_DURATIONS } from '../constants';

/**
 * useSimulationPoll Hook
 *
 * Manages full result polling for risk simulations with intelligent backoff
 *
 * **Features**:
 * - Fetch complete simulation results
 * - Exponential backoff on errors
 * - Automatic fallback to cached data
 * - Connection state tracking
 * - Customizable polling
 * - Manual fetch capability
 *
 * **Polling Strategies**:
 * 1. **Normal**: Poll at configured interval
 * 2. **Degraded**: On error, increase interval and use cache
 * 3. **Offline**: Use cached data, attempt periodic reconnect
 * 4. **Manual**: User controls fetch
 *
 * **Usage**:
 * ```tsx
 * const {
 *   result,
 *   isPolling,
 *   isConnected,
 *   error,
 *   progress,
 *   pause,
 *   resume,
 *   refetch
 * } = useSimulationPoll('sim-123', {
 *   autoStart: true,
 *   interval: 5000,
 *   onCompleted: (result) => showResults(result)
 * });
 *
 * return (
 *   <>
 *     <ResultsViewer result={result} />
 *     <ProgressBar value={result?.progress ?? 0} />
 *     <Button onClick={isPolling ? pause : resume}>
 *       {isPolling ? 'Pause' : 'Resume'}
 *     </Button>
 *   </>
 * );
 * ```
 *
 * **Data Flow**:
 * - Poll API → Get result → Update UI
 * - On error → Try cache → Show fallback
 * - On completion → Stop polling → Notify
 *
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 7.1: Result Polling)
 */
export function useSimulationPoll(
  simulationId: string,
  options?: {
    /**
     * Start polling immediately (default: true)
     */
    autoStart?: boolean;

    /**
     * Poll interval in milliseconds (default: 5000)
     */
    interval?: number;

    /**
     * Maximum retries (default: 5)
     */
    maxRetries?: number;

    /**
     * Backoff factor (default: 2)
     */
    backoffFactor?: number;

    /**
     * Include detailed risk points (default: false)
     */
    includeDetails?: boolean;

    /**
     * Callback when result updated
     */
    onUpdated?: (result: RiskSimulationResult) => void;

    /**
     * Callback on completion
     */
    onCompleted?: (result: RiskSimulationResult) => void;

    /**
     * Callback on error
     */
    onError?: (error: Error, retryCount: number) => void;

    /**
     * Callback when connection status changes
     */
    onConnectionChange?: (isConnected: boolean) => void;
  }
) {
  const {
    autoStart = true,
    interval = 5000,
    maxRetries = 5,
    backoffFactor = 2,
    includeDetails = false,
    onUpdated,
    onCompleted,
    onError,
    onConnectionChange,
  } = options || {};

  const [result, setResult] = useState<RiskSimulationResult | null>(null);
  const [isPolling, setIsPolling] = useState(autoStart);
  const [isConnected, setIsConnected] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [fallbackData, setFallbackData] = useState<RiskSimulationResult | null>(null);

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
    return interval * Math.pow(backoffFactor, Math.min(retryCount, 3));
  }, [interval, backoffFactor, retryCount]);

  const poll = useCallback(async () => {
    try {
      const newResult = await fetchSimulationResult(simulationId, {
        includeDetails,
        cacheTimeout: CACHE_DURATIONS.RESULT,
      });

      setResult(newResult);
      setError(null);
      setRetryCount(0);
      setFallbackData(null);

      // Update connection status
      if (!isConnectedRef.current) {
        setIsConnected(true);
        onConnectionChange?.(true);
      }

      onUpdated?.(newResult);

      // Check completion
      if (
        newResult.status === 'completed' ||
        newResult.status === 'failed' ||
        newResult.status === 'cancelled'
      ) {
        setIsPolling(false);
        onCompleted?.(newResult);
      }
    } catch (err) {
      const error =
        err instanceof Error ? err : new Error('Result poll failed');
      setError(error);

      const nextRetryCount = retryCountRef.current + 1;
      setRetryCount(nextRetryCount);

      // Try to use cached data
      try {
        const cached = localStorage.getItem(`risk_result_${simulationId}`);
        if (cached) {
          const parsed = JSON.parse(cached) as {
            data: RiskSimulationResult;
            timestamp: number;
          };
          setFallbackData(parsed.data);
          console.warn(
            '[useSimulationPoll] Using cached data after error:',
            error.message
          );
        }
      } catch {
        // Cache read failed
      }

      if (nextRetryCount >= maxRetries) {
        // Max retries exceeded
        if (isConnectedRef.current) {
          setIsConnected(false);
          onConnectionChange?.(false);
        }
      }

      onError?.(error, nextRetryCount);
    }
  }, [simulationId, includeDetails, maxRetries, onUpdated, onCompleted, onError, onConnectionChange]);

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

    // Schedule next poll
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
    setRetryCount(0);
  }, []);

  const refetch = useCallback(async () => {
    await poll();
  }, [poll]);

  return {
    /**
     * Current simulation result
     */
    result: result ?? fallbackData,

    /**
     * All results including cached
     */
    allResults: result ?? fallbackData,

    /**
     * Is polling active
     */
    isPolling,

    /**
     * Is connected to API
     */
    isConnected,

    /**
     * Using fallback/cached data
     */
    isFallback: !result && fallbackData !== null,

    /**
     * Last error
     */
    error,

    /**
     * Current retry count
     */
    retryCount,

    /**
     * Current poll interval
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
     * Manual fetch
     */
    refetch,

    /**
     * Reset state
     */
    reset: () => {
      setResult(null);
      setError(null);
      setRetryCount(0);
      setIsConnected(true);
      setFallbackData(null);
    },
  };
}

export default useSimulationPoll;
