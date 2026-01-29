/**
 * useApiError Hook
 * Centralized error handling for API calls with resilience patterns
 * 
 * This hook provides:
 * - Error categorization (401, 429, 500, network, etc.)
 * - Automatic retry logic with exponential backoff
 * - User-friendly error messages
 * - Toast notifications
 * - Offline detection and handling
 * 
 * @usage
 * const { handleError, isOffline } = useApiError();
 * 
 * try {
 *   await apiCall();
 * } catch (error) {
 *   handleError(error);
 * }
 */

import { useCallback, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  handleApiError,
  calculateRetryDelay,
  isOfflineError,
  type ErrorHandlingStrategy,
} from '@/lib/error-handler';
import { useRouter } from 'next/navigation';

interface UseApiErrorOptions {
  onUnauthorized?: () => void;
  onRateLimited?: () => void;
  onServerError?: () => void;
  onNetworkError?: () => void;
  showToast?: boolean;
}

/**
 * Hook for handling API errors with automatic retry and user notifications
 * @param options - Configuration options for error handling
 * @returns Error handling utilities
 */
export function useApiError(options: UseApiErrorOptions = {}) {
  const queryClient = useQueryClient();
  const router = useRouter();
  const retryCountRef = useRef<Map<string, number>>(new Map());

  const {
    onUnauthorized,
    onRateLimited,
    onServerError,
    onNetworkError,
    showToast = true,
  } = options;

  /**
   * Generate a unique key for retry tracking
   */
  const getRetryKey = useCallback((error: any): string => {
    const status = error?.response?.status || 0;
    const message = error?.message || 'unknown';
    return `${status}-${message}`;
  }, []);

  /**
   * Get current retry count for an error
   */
  const getRetryCount = useCallback(
    (error: any): number => {
      const key = getRetryKey(error);
      return retryCountRef.current.get(key) || 0;
    },
    [getRetryKey]
  );

  /**
   * Increment retry count for an error
   */
  const incrementRetryCount = useCallback(
    (error: any): void => {
      const key = getRetryKey(error);
      const current = retryCountRef.current.get(key) || 0;
      retryCountRef.current.set(key, current + 1);
    },
    [getRetryKey]
  );

  /**
   * Reset retry count for an error
   */
  const resetRetryCount = useCallback(
    (error: any): void => {
      const key = getRetryKey(error);
      retryCountRef.current.delete(key);
    },
    [getRetryKey]
  );

  /**
   * Clear all retry counts (useful for logout)
   */
  const clearAllRetries = useCallback((): void => {
    retryCountRef.current.clear();
  }, []);

  /**
   * Handle an API error and determine appropriate action
   */
  const handleError = useCallback(
    async (error: any, context?: { url?: string; method?: string }) => {
      const retryCount = getRetryCount(error);
      const { category, strategy, userMessage } = handleApiError(error, retryCount);

      // Show user-friendly message as toast
      if (showToast) {
        if (category === 'UNAUTHORIZED') {
          toast.error('Session expired', {
            description: userMessage,
          });
        } else if (category === 'RATE_LIMITED') {
          toast.warning('Rate limited', {
            description: userMessage,
          });
        } else if (category === 'SERVER_ERROR') {
          toast.error('Server error', {
            description: userMessage,
          });
        } else if (category === 'NETWORK_ERROR') {
          toast.error('Connection lost', {
            description: userMessage,
          });
        } else if (category !== 'UNKNOWN') {
          toast.error('Error', {
            description: userMessage,
          });
        }
      }

      // Execute category-specific callbacks
      switch (category) {
        case 'UNAUTHORIZED':
          onUnauthorized?.();
          // Redirect to login
          router.push('/login');
          break;

        case 'RATE_LIMITED':
          onRateLimited?.();
          incrementRetryCount(error);
          break;

        case 'SERVER_ERROR':
          onServerError?.();
          incrementRetryCount(error);
          break;

        case 'NETWORK_ERROR':
          onNetworkError?.();
          // Don't count network errors in retry tracking
          break;

        default:
          // No specific action needed
          break;
      }

      // Invalidate related queries on offline
      if (isOfflineError(error)) {
        // Keep stale data available until reconnection
        // Don't invalidate queries, let them use cached data
      }

      return {
        category,
        strategy,
        userMessage,
        retryCount,
        shouldRetry: strategy.action === 'retry' && retryCount < (strategy.maxRetries ?? 3),
        retryDelay:
          strategy.action === 'retry'
            ? calculateRetryDelay(retryCount, strategy.retryDelay)
            : 0,
      };
    },
    [
      getRetryCount,
      incrementRetryCount,
      showToast,
      onUnauthorized,
      onRateLimited,
      onServerError,
      onNetworkError,
      router,
    ]
  );

  /**
   * Retry an async operation with exponential backoff
   */
  const retryAsync = useCallback(
    async <T,>(
      fn: () => Promise<T>,
      maxRetries: number = 3,
      baseDelay: number = 1000
    ): Promise<T> => {
      let lastError: any;

      for (let i = 0; i < maxRetries; i++) {
        try {
          return await fn();
        } catch (error) {
          lastError = error;

          // Check if error is retryable
          if (!isRetryableError(error) || i === maxRetries - 1) {
            throw error;
          }

          // Calculate delay with exponential backoff
          const delay = calculateRetryDelay(i, baseDelay);
          await new Promise((resolve) => setTimeout(resolve, delay));
        }
      }

      throw lastError;
    },
    []
  );

  /**
   * Check if we're currently offline
   */
  const checkOfflineStatus = useCallback((): boolean => {
    return typeof navigator !== 'undefined'
      ? !navigator.onLine
      : false;
  }, []);

  /**
   * Listen for online/offline events
   */
  const setupOfflineListener = useCallback(
    (onOffline?: () => void, onOnline?: () => void): (() => void) => {
      const handleOffline = () => {
        onOffline?.();
      };

      const handleOnline = () => {
        // Refetch all queries when coming back online
        queryClient.refetchQueries();
        onOnline?.();
      };

      if (typeof window === 'undefined') {
        return () => {};
      }

      window.addEventListener('offline', handleOffline);
      window.addEventListener('online', handleOnline);

      return () => {
        window.removeEventListener('offline', handleOffline);
        window.removeEventListener('online', handleOnline);
      };
    },
    [queryClient]
  );

  return {
    // Error handling
    handleError,
    getRetryCount,
    incrementRetryCount,
    resetRetryCount,
    clearAllRetries,

    // Retry utilities
    retryAsync,

    // Offline detection
    isOffline: checkOfflineStatus(),
    checkOfflineStatus,
    setupOfflineListener,

    // Query client for advanced usage
    queryClient,
  };
}

/**
 * Helper to check if an error is retryable
 */
function isRetryableError(error: any): boolean {
  if (!error) return false;

  const status = error?.response?.status || 0;
  const retryableStatuses = [408, 429, 500, 502, 503, 504];

  if (retryableStatuses.includes(status)) return true;

  const message = (error?.message || '').toLowerCase();
  const networkErrors = ['network', 'timeout', 'econnrefused', 'enotfound', 'econnaborted'];

  return networkErrors.some((err) => message.includes(err));
}

/**
 * Hook to create an error handler with preset options
 * Useful for specific error handling patterns
 */
export function useApiErrorWithDefaults() {
  return useApiError({
    showToast: true,
    onUnauthorized: () => {
      // Logout logic would go here (handled by redirect in handleError)
    },
    onRateLimited: () => {
      // Could emit analytics event
    },
    onServerError: () => {
      // Could emit analytics event
    },
    onNetworkError: () => {
      // Could trigger sync queue or offline mode
    },
  });
}
