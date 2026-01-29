'use client';

import { useState, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchWeatherGrid, cacheWeatherGrid, getCachedWeatherGrid } from '../api';
import type { WeatherGrid } from '../types';

/**
 * useWeatherGrid Hook
 *
 * Manages weather grid data fetching and caching
 *
 * **Features**:
 * - Automatic grid fetching with configurable bounds
 * - Cache management (localStorage + query cache)
 * - Error handling with fallback to cached data
 * - Refetch capabilities
 * - Loading states
 *
 * **Usage**:
 * ```tsx
 * const { grid, isLoading, error, refetch } = useWeatherGrid({
 *   bounds: {
 *     north: 40.8,
 *     south: 40.7,
 *     east: -73.9,
 *     west: -74.0
 *   },
 *   enabled: true,
 *   staleTime: 5 * 60 * 1000
 * });
 *
 * if (isLoading) return <LoadingSpinner />;
 * if (error) return <ErrorBanner error={error} />;
 *
 * return <GridVisualization grid={grid} />;
 * ```
 *
 * **Fallback Behavior**:
 * 1. Try to fetch from API
 * 2. On error, check query cache
 * 3. On cache miss, check localStorage
 * 4. If all fail, return error
 *
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 6.1: Weather Grid)
 */
export function useWeatherGrid(options?: {
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
   * Enable/disable query
   */
  enabled?: boolean;

  /**
   * Cache duration (ms)
   */
  staleTime?: number;

  /**
   * Refetch interval (ms)
   */
  refetchInterval?: number;

  /**
   * Include forecast data
   */
  includeForecast?: boolean;

  /**
   * Grid resolution override
   */
  resolution?: number;

  /**
   * Custom error handler
   */
  onError?: (error: Error) => void;
}) {
  const {
    bounds,
    enabled = true,
    staleTime = 5 * 60 * 1000,
    refetchInterval = undefined,
    includeForecast = false,
    resolution,
    onError,
  } = options || {};

  const [fallbackData, setFallbackData] = useState<WeatherGrid | null>(null);

  const query = useQuery({
    queryKey: [
      'weather-grid',
      bounds?.north,
      bounds?.south,
      bounds?.east,
      bounds?.west,
      resolution,
      includeForecast,
    ],
    queryFn: async () => {
      try {
        const grid = await fetchWeatherGrid({
          bounds,
          resolution,
          includeForecast,
        });

        // Save to localStorage for offline access
        cacheWeatherGrid(grid);
        setFallbackData(null);

        return grid;
      } catch (error) {
        // Try to get cached data on error
        const cached = getCachedWeatherGrid();
        if (cached) {
          setFallbackData(cached);
          console.warn(
            '[useWeatherGrid] Using cached grid after fetch error:',
            error instanceof Error ? error.message : String(error)
          );
        }

        throw error;
      }
    },
    enabled,
    staleTime,
    refetchInterval,
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

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

  return {
    /**
     * Weather grid data
     */
    grid: query.data ?? fallbackData,

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
     * Whether using fallback data
     */
    isFallback: !query.data && fallbackData !== null,

    /**
     * Refetch function
     */
    refetch: query.refetch,

    /**
     * Query status
     */
    status: query.status,
  };
}

export default useWeatherGrid;
