'use client';

import { useState, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchWeatherAlerts } from '../api';
import type { WeatherAlert } from '../types';

/**
 * useAlerts Hook
 *
 * Manages weather alerts fetching and real-time updates
 *
 * **Features**:
 * - Fetch active weather alerts for area
 * - Filter by severity and type
 * - Real-time alert subscriptions
 * - Alert acknowledgment/dismissal
 * - Severity sorting
 * - Count tracking
 *
 * **Usage**:
 * ```tsx
 * const { alerts, isLoading, criticalCount, dismiss } = useAlerts({
 *   area: bounds,
 *   minSeverity: 3,
 *   onNewAlert: (alert) => playSound('/alert.mp3')
 * });
 *
 * return (
 *   <div>
 *     <AlertBanner alert={alerts[0]} onDismiss={dismiss} />
 *     <span>Critical Alerts: {criticalCount}</span>
 *   </div>
 * );
 * ```
 *
 * **Alert Priorities**:
 * - Severity 5: Critical (immediate action required)
 * - Severity 4: Severe (caution advised)
 * - Severity 3: Moderate (be aware)
 * - Severity 2: Minor (informational)
 * - Severity 1: Advisory (low priority)
 *
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 6.2: Alert System)
 */
export function useAlerts(options?: {
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
   * Minimum severity (1-5)
   */
  minSeverity?: number;

  /**
   * Enable/disable fetching
   */
  enabled?: boolean;

  /**
   * Refetch interval (ms)
   */
  refetchInterval?: number;

  /**
   * Callback for new alerts
   */
  onNewAlert?: (alert: WeatherAlert) => void;

  /**
   * Callback for dismissed alerts
   */
  onDismiss?: (alertId: string) => void;

  /**
   * Custom error handler
   */
  onError?: (error: Error) => void;
}) {
  const {
    area,
    type,
    minSeverity,
    enabled = true,
    refetchInterval = 60000, // Refetch every minute
    onNewAlert,
    onError,
  } = options || {};

  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(
    new Set()
  );

  const query = useQuery({
    queryKey: [
      'weather-alerts',
      area?.north,
      area?.south,
      area?.east,
      area?.west,
      type,
      minSeverity,
    ],
    queryFn: async () => {
      const alerts = await fetchWeatherAlerts({
        area,
        type,
        minSeverity,
        onlyActive: true,
      });

      // Check for new alerts
      if (query.data) {
        const newAlerts = alerts.filter(
          (a) => !query.data!.some((existing) => existing.id === a.id)
        );
        newAlerts.forEach((alert) => {
          onNewAlert?.(alert);
        });
      }

      return alerts;
    },
    enabled,
    staleTime: 30000, // 30 seconds
    refetchInterval,
    retry: 1,
  });

  const handleDismiss = useCallback((alertId: string) => {
    setDismissedAlerts((prev) => {
      const next = new Set(prev);
      next.add(alertId);
      return next;
    });
    options?.onDismiss?.(alertId);
  }, [options]);

  const handleError = useCallback(() => {
    if (query.error && onError) {
      onError(
        query.error instanceof Error
          ? query.error
          : new Error(String(query.error))
      );
    }
  }, [query.error, onError]);

  useEffect(() => {
    handleError();
  }, [query.error, handleError]);

  // Filter out dismissed alerts
  const visibleAlerts = (query.data ?? []).filter(
    (alert) => !dismissedAlerts.has(alert.id)
  );

  // Sort by severity (highest first)
  const sortedAlerts = [...visibleAlerts].sort(
    (a, b) => b.severity - a.severity
  );

  // Count critical alerts (severity 5)
  const criticalCount = sortedAlerts.filter((a) => a.severity === 5).length;

  // Count severe alerts (severity 4+)
  const severeCount = sortedAlerts.filter((a) => a.severity >= 4).length;

  return {
    /**
     * Active alerts (visible, not dismissed)
     */
    alerts: sortedAlerts,

    /**
     * All alerts including dismissed
     */
    allAlerts: query.data ?? [],

    /**
     * Loading state
     */
    isLoading: query.isLoading,

    /**
     * Error object
     */
    error: query.error
      ? query.error instanceof Error
        ? query.error
        : new Error(String(query.error))
      : null,

    /**
     * Number of critical alerts
     */
    criticalCount,

    /**
     * Number of severe alerts (severity >= 4)
     */
    severeCount,

    /**
     * Total visible alert count
     */
    count: sortedAlerts.length,

    /**
     * Check if specific alert is dismissed
     */
    isDismissed: (alertId: string) => dismissedAlerts.has(alertId),

    /**
     * Dismiss alert from view
     */
    dismiss: handleDismiss,

    /**
     * Restore dismissed alert
     */
    restore: (alertId: string) => {
      setDismissedAlerts((prev) => {
        const next = new Set(prev);
        next.delete(alertId);
        return next;
      });
    },

    /**
     * Clear all dismissed alerts
     */
    clearDismissed: () => setDismissedAlerts(new Set()),

    /**
     * Refetch alerts
     */
    refetch: query.refetch,

    /**
     * Query status
     */
    status: query.status,
  };
}

export default useAlerts;
