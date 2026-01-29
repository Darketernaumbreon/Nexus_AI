/**
 * useTokenRefresh Hook
 * Silent token refresh before expiry
 * 
 * **Pattern**: AUTOMATED token refresh via polling
 * - Checks token expiry every 30 seconds
 * - Refreshes token 5 minutes before actual expiry
 * - Handles refresh failures with exponential backoff
 * 
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 6.1: Polling Pattern)
 */

'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { AuthAPI } from '../api';
import { useApiError } from '@/hooks/use-api-error';

import type { AuthResponse } from '../types';

/**
 * Options for useTokenRefresh hook
 */
export interface UseTokenRefreshOptions {
  /**
   * Enable auto-refresh (default: true)
   */
  enabled?: boolean;

  /**
   * Check interval in milliseconds (default: 30000 = 30 seconds)
   */
  checkInterval?: number;

  /**
   * Refresh when time remaining is less than this (seconds)
   * Default: 300 (5 minutes) - refresh 5 min before expiry
   */
  refreshThreshold?: number;

  /**
   * Callback when token is refreshed successfully
   */
  onTokenRefreshed?: (data: AuthResponse) => void;

  /**
   * Callback when refresh fails
   */
  onRefreshFailed?: (error: Error) => void;

  /**
   * Show toast notifications (default: true)
   */
  showNotifications?: boolean;
}

/**
 * useTokenRefresh Hook
 *
 * Automatically refreshes JWT token before expiry
 *
 * **Behavior**:
 * 1. Checks token every 30 seconds
 * 2. If expiring within 5 minutes, initiates refresh
 * 3. On refresh success: updates token, continues polling
 * 4. On refresh failure (401): clears session, redirects to login
 * 5. On network error: retries with exponential backoff
 *
 * **Usage**:
 * ```tsx
 * // Auto-refresh enabled by default
 * useTokenRefresh({
 *   onTokenRefreshed: () => console.log('Token refreshed'),
 *   onRefreshFailed: () => console.log('Refresh failed'),
 * });
 * ```
 *
 * **Connection Points**:
 * - Used by: useSessionGuard() hook
 * - Calls: AuthAPI.refreshToken()
 * - Monitors: JWT expiry via AuthAPI.getTokenExpiryTime()
 * - Handles: Network errors via use-api-error hook
 */
export function useTokenRefresh(options: UseTokenRefreshOptions = {}) {
  const {
    enabled = true,
    checkInterval = 30 * 1000, // 30 seconds
    refreshThreshold = 5 * 60, // 5 minutes in seconds
    onTokenRefreshed,
    onRefreshFailed,
    showNotifications = true,
  } = options;

  const queryClient = useQueryClient();
  const { handleError, retryAsync } = useApiError();

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isRefreshingRef = useRef(false);
  const retryCountRef = useRef(0);
  const maxRetriesRef = useRef(3);

  /**
   * Attempt to refresh token
   */
  const attemptTokenRefresh = useCallback(async (): Promise<boolean> => {
    if (isRefreshingRef.current) {
      return false; // Already refreshing, skip
    }

    try {
      isRefreshingRef.current = true;

      // Get current refresh token
      const token = AuthAPI.retrieveToken();
      if (!token) {
        return false; // No token to refresh
      }

      // Attempt refresh with retries
      const result = await retryAsync(
        () => {
          // Mock refresh - in real app would extract refresh_token from storage
          return AuthAPI.refreshToken(token);
        },
        3,  // maxRetries
        1000  // baseDelay
      );

      if (result) {
        // ✅ Token refreshed successfully
        retryCountRef.current = 0; // Reset retry counter
        
        if (showNotifications) {
          toast.success('Session refreshed');
        }

        // Invalidate queries to refetch with new token
        queryClient.invalidateQueries();

        onTokenRefreshed?.(result as any);
        return true;
      }

      return false;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));

      // Handle refresh failure
      retryCountRef.current++;

      if (retryCountRef.current >= maxRetriesRef.current) {
        // Max retries exceeded, session is invalid
        if (showNotifications) {
          toast.error('Session expired. Please login again.');
        }

        AuthAPI.removeToken();
        queryClient.invalidateQueries();
        onRefreshFailed?.(err);

        return false;
      }

      // Still have retries left, will try again on next check
      handleError(err);

      return false;
    } finally {
      isRefreshingRef.current = false;
    }
  }, [queryClient, onTokenRefreshed, onRefreshFailed, handleError, showNotifications]);

  /**
   * Check if token needs refresh
   */
  const shouldRefreshToken = useCallback((): boolean => {
    try {
      const token = AuthAPI.retrieveToken();
      if (!token) return false;

      // Get time remaining in seconds
      const timeRemaining = AuthAPI.getTokenExpiryTime(token);

      // Refresh if expiring soon
      return timeRemaining > 0 && timeRemaining < refreshThreshold;
    } catch {
      return false;
    }
  }, [refreshThreshold]);

  /**
   * Setup polling interval
   */
  useEffect(() => {
    if (!enabled) {
      // Cleanup if disabled
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    // Initial check
    if (shouldRefreshToken()) {
      attemptTokenRefresh();
    }

    // Setup polling
    intervalRef.current = setInterval(() => {
      if (shouldRefreshToken()) {
        attemptTokenRefresh();
      }
    }, checkInterval);

    // Cleanup
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [enabled, checkInterval, shouldRefreshToken, attemptTokenRefresh]);

  /**
   * Manual refresh function (can be called by parent)
   */
  const manualRefresh = useCallback(async (): Promise<boolean> => {
    return attemptTokenRefresh();
  }, [attemptTokenRefresh]);

  return {
    manualRefresh,
    shouldRefreshToken,
    isRefreshing: isRefreshingRef.current,
    retryCount: retryCountRef.current,
  };
}
