'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { getSimulationStatus } from '../api';
import type { SimulationStatus } from '../types';
import { DEFAULT_POLLING_CONFIG } from '../constants';

/**
 * useSimulationStatus Hook
 *
 * Manages lightweight status polling for simulations
 *
 * **Features**:
 * - Lightweight status endpoint polling
 * - Progress tracking
 * - Error detection and recovery
 * - Automatic stop on completion
 * - Customizable intervals
 * - Connection state tracking
 *
 * **Usage**:
 * ```tsx
 * const { status, progress, isPolling, error, pause, resume } = useSimulationStatus('sim-123', {
 *   autoStart: true,
 *   interval: 2000,
 *   onProgress: (progress) => updateProgressBar(progress),
 *   onComplete: (status) => showCompletion(status)
 * });
 *
 * return (
 *   <div>
 *     <ProgressBar value={progress} />
 *     <StatusBadge status={status} />
 *   </div>
 * );
 * ```
 *
 * **Status Flow**:
 * - `initializing` → `running` → `completed` | `failed`
 * - Can pause/resume polling
 * - Auto-stops on completion or cancellation
 *
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 7.1: Status Tracking)
 */
export function useSimulationStatus(
  simulationId: string,
  options?: {
    /**
     * Start polling immediately (default: true)
     */
    autoStart?: boolean;

    /**
     * Poll interval in milliseconds (default: 2000)
     */
    interval?: number;

    /**
     * Maximum retries on failure (default: 3)
     */
    maxRetries?: number;

    /**
     * Backoff factor (default: 1.5)
     */
    backoffFactor?: number;

    /**
     * Callback on progress update
     */
    onProgress?: (progress: number) => void;

    /**
     * Callback on status change
     */
    onStatusChange?: (status: SimulationStatus) => void;

    /**
     * Callback on completion
     */
    onComplete?: (status: SimulationStatus) => void;

    /**
     * Callback on error
     */
    onError?: (error: Error, retryCount: number) => void;

    /**
     * Manual stop callback
     */
    onStop?: () => void;
  }
) {
  const {
    autoStart = true,
    interval = 2000,
    maxRetries = 3,
    backoffFactor = 1.5,
    onProgress,
    onStatusChange,
    onComplete,
    onError,
    onStop,
  } = options || {};

  const [status, setStatus] = useState<SimulationStatus>('idle');
  const [progress, setProgress] = useState(0);
  const [isPolling, setIsPolling] = useState(autoStart);
  const [error, setError] = useState<Error | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const statusRef = useRef(status);
  const retryCountRef = useRef(retryCount);

  // Keep refs in sync
  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  useEffect(() => {
    retryCountRef.current = retryCount;
  }, [retryCount]);

  const calculateInterval = useCallback(() => {
    return interval * Math.pow(backoffFactor, Math.min(retryCount, 3));
  }, [interval, backoffFactor, retryCount]);

  const poll = useCallback(async () => {
    try {
      const result = await getSimulationStatus(simulationId);

      setStatus(result.status as SimulationStatus);
      setProgress(result.progress ?? 0);
      setError(null);
      setRetryCount(0);

      onProgress?.(result.progress ?? 0);
      onStatusChange?.(result.status as SimulationStatus);

      // Check completion
      if (
        result.status === 'completed' ||
        result.status === 'failed' ||
        result.status === 'cancelled'
      ) {
        setIsPolling(false);
        onComplete?.(result.status as SimulationStatus);
      }
    } catch (err) {
      const error =
        err instanceof Error ? err : new Error('Status poll failed');
      setError(error);

      const nextRetryCount = retryCountRef.current + 1;
      setRetryCount(nextRetryCount);

      if (nextRetryCount >= maxRetries) {
        setIsPolling(false);
        onError?.(error, nextRetryCount);
      }
    }
  }, [simulationId, maxRetries, onProgress, onStatusChange, onComplete, onError]);

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
    onStop?.();
  }, [onStop]);

  const resume = useCallback(() => {
    setIsPolling(true);
    setRetryCount(0);
  }, []);

  return {
    /**
     * Current simulation status
     */
    status,

    /**
     * Simulation progress (0-100)
     */
    progress,

    /**
     * Is polling active
     */
    isPolling,

    /**
     * Last error
     */
    error,

    /**
     * Current retry count
     */
    retryCount,

    /**
     * Current poll interval (adjusted for backoff)
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
     * Reset state
     */
    reset: () => {
      setStatus('idle');
      setProgress(0);
      setError(null);
      setRetryCount(0);
    },
  };
}

export default useSimulationStatus;
