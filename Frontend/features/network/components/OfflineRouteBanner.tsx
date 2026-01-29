'use client';

import React from 'react';
import { AlertCircle, Wifi } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';

import type { RoutePolyline } from '../types';

/**
 * Props for OfflineRouteBanner component
 */
export interface OfflineRouteBannerProps {
  /**
   * Route data
   */
  route: RoutePolyline;

  /**
   * Whether to show the banner (control visibility)
   */
  show?: boolean;

  /**
   * Callback when user dismisses banner
   */
  onDismiss?: () => void;

  /**
   * Callback when user attempts to sync
   */
  onSync?: () => void;

  /**
   * Whether sync is in progress
   */
  isSyncing?: boolean;
}

/**
 * OfflineRouteBanner Component
 *
 * Visual indicator when route data comes from offline backup
 *
 * **Scenario**: When primary API fails (network error, server down)
 * - Route data source switches to internal_postgis (offline backup)
 * - User sees warning banner explaining the situation
 * - Option to refresh/sync when connection restored
 *
 * **Pattern**: MANUAL user interaction with AUTOMATED fallback
 * ```
 * Primary API fails → Fallback to offline → Show banner
 * User clicks Sync → Retry primary API
 * ```
 *
 * **Data Indicator**:
 * - Shows: "Using Offline Backup Route"
 * - Source badge: Displays current source (primary/offline/cached)
 * - Warning icon: Indicates non-optimal state
 *
 * **Usage**:
 * ```tsx
 * <OfflineRouteBanner
 *   route={selectedRoute}
 *   show={route.source === 'internal_postgis'}
 *   onSync={handleSync}
 *   isSyncing={isRefreshing}
 * />
 * ```
 *
 * **Connection Points**:
 * - Parent: RoadNetworkMap.tsx (Phase 5)
 * - Data from: useRouteDetails hook (with fallback)
 * - Action: Trigger useOfflineBackupRoute().refetch()
 *
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 5.2.2: Offline Fallback)
 */
export const OfflineRouteBanner = React.memo(
  ({
    route,
    show = true,
    onDismiss,
    onSync,
    isSyncing = false,
  }: OfflineRouteBannerProps) => {
    if (!show || !route) {
      return null;
    }

    const isOfflineSource = route.source === 'internal_postgis';

    if (!isOfflineSource) {
      return null;
    }

    return (
      <Alert className="border-amber-200 bg-amber-50 mb-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
          
          <div className="flex-1 min-w-0">
            <AlertTitle className="text-amber-900 mb-1">
              Using Offline Backup Route
            </AlertTitle>
            
            <AlertDescription className="text-amber-800 text-sm mb-2">
              You're viewing "{route.name}" from local backup. The primary connection is unavailable.
              When your connection is restored, sync to get the latest data.
            </AlertDescription>

            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="outline" className="bg-white border-amber-300">
                <Wifi className="h-3 w-3 mr-1" />
                {route.source === 'internal_postgis' ? 'Offline' : 'Cached'}
              </Badge>

              {route.updated_at && (
                <span className="text-xs text-amber-700">
                  Last updated: {new Date(route.updated_at).toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>

          <div className="flex gap-2 flex-shrink-0">
            {onSync && (
              <button
                onClick={onSync}
                disabled={isSyncing}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                  isSyncing
                    ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                    : 'bg-amber-600 text-white hover:bg-amber-700 active:bg-amber-800'
                }`}
              >
                {isSyncing ? 'Syncing...' : 'Sync Now'}
              </button>
            )}

            {onDismiss && (
              <button
                onClick={onDismiss}
                className="px-3 py-1 rounded text-xs font-medium text-amber-700 hover:bg-amber-100 transition-colors"
                aria-label="Dismiss banner"
              >
                ✕
              </button>
            )}
          </div>
        </div>
      </Alert>
    );
  }
);

OfflineRouteBanner.displayName = 'OfflineRouteBanner';

export default OfflineRouteBanner;
