/**
 * useRouteDetails Hook
 * Fetch and manage detailed route information
 * 
 * Query: GET /network/routes/{id}
 * Response: RoutePolyline with segments and risk scores
 * 
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 5.2.3: State & Props)
 */

'use client';

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { NetworkAPI } from '../api';

import type { RoutePolyline } from '../types';

/**
 * Query key for route details
 */
export const routeDetailsQueryKey = (routeId: string) => ['routes', routeId] as const;

/**
 * useRouteDetails Hook
 *
 * Fetches complete route polylines with segments and risk scores
 *
 * **Usage**:
 * ```tsx
 * const { data: route, isLoading, error } = useRouteDetails('NH-06');
 *
 * return (
 *   <>
 *     {isLoading && <Skeleton />}
 *     {error && <Error message={error.message} />}
 *     {route && <RouteMap segments={route.segments} />}
 *   </>
 * );
 * ```
 *
 * **Caching**:
 * - Stale time: 5 minutes
 * - Retry: 2 times with exponential backoff
 * - Background refetch: Enabled
 *
 * **Connection Points**:
 * - Called by: features/network/components/RoadNetworkMap.tsx
 * - Calls: NetworkAPI.getRouteDetails()
 * - Data used by: RiskRoute, NodeDetails components
 */
export function useRouteDetails(
  routeId: string | null,
  options: {
    enabled?: boolean;
    staleTime?: number;
  } = {}
) {
  const { enabled = true, staleTime = 5 * 60 * 1000 } = options;

  const query = useQuery({
    queryKey: routeDetailsQueryKey(routeId || ''),
    queryFn: async () => {
      if (!routeId) throw new Error('Route ID required');
      return NetworkAPI.getRouteDetails(routeId);
    },
    enabled: !!routeId && enabled,
    staleTime,
    retry: 2,
    refetchOnWindowFocus: false,
  });

  return {
    route: query.data as RoutePolyline | undefined,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    error: query.error as Error | null,
    refetch: query.refetch,
  };
}

/**
 * useRouteRiskScores Hook
 * Fetch risk scores for route segments (often separate endpoint)
 */
export function useRouteRiskScores(
  routeId: string | null,
  options: {
    enabled?: boolean;
  } = {}
) {
  const { enabled = true } = options;

  const query = useQuery({
    queryKey: ['routes', routeId, 'risk-scores'],
    queryFn: async () => {
      if (!routeId) throw new Error('Route ID required');
      return NetworkAPI.getRouteRiskScores(routeId);
    },
    enabled: !!routeId && enabled,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });

  return {
    segments: query.data || [],
    isLoading: query.isLoading,
    error: query.error as Error | null,
    refetch: query.refetch,
  };
}

/**
 * useOfflineBackupRoute Hook
 * Fetch offline backup route if primary API fails
 */
export function useOfflineBackupRoute(
  routeId: string | null,
  options: {
    enabled?: boolean;
    fallbackToOffline?: boolean;
  } = {}
) {
  const { enabled = true, fallbackToOffline = true } = options;

  const query = useQuery({
    queryKey: ['routes', routeId, 'offline-backup'],
    queryFn: async () => {
      if (!routeId) throw new Error('Route ID required');
      return NetworkAPI.getOfflineBackupRoute(routeId);
    },
    enabled: !!routeId && enabled && fallbackToOffline,
    staleTime: 1000 * 60 * 60, // 1 hour (less frequent updates)
    retry: 1,
  });

  return {
    backupRoute: query.data as RoutePolyline | null | undefined,
    isLoading: query.isLoading,
    error: query.error as Error | null,
    isAvailable: !!query.data,
  };
}

/**
 * Helper: Invalidate route details cache
 */
export function useInvalidateRouteDetails(routeId?: string) {
  const queryClient = useQueryClient();

  return () => {
    if (routeId) {
      queryClient.invalidateQueries({
        queryKey: routeDetailsQueryKey(routeId),
      });
    } else {
      // Invalidate all routes
      queryClient.invalidateQueries({
        queryKey: ['routes'],
      });
    }
  };
}
