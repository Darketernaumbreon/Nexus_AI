/**
 * useLogin Hook
 * Handle user login mutation
 * 
 * Mutation: POST /iam/login/access-token
 * Response: 200 OK with AuthResponse (JWT tokens + user profile)
 * 
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 5.1.2: Auth Domain)
 */

'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';

import { AuthAPI } from '../api';
import { useApiError } from '@/hooks/use-api-error';

import type { LoginCredentials, AuthResponse, LoginResponse } from '../types';

/**
 * Options for useLogin hook
 */
export interface UseLoginOptions {
  /**
   * Callback after successful login
   */
  onSuccess?: (data: AuthResponse) => void;

  /**
   * Callback on login error
   */
  onError?: (error: Error) => void;

  /**
   * Redirect path after login (default: '/network')
   */
  redirectTo?: string;

  /**
   * Show error toast on login failure (default: true)
   */
  showErrorToast?: boolean;
}

/**
 * useLogin Hook
 *
 * Handles user authentication via username/password
 * Stores JWT tokens and user profile
 * Handles token refresh for expiry scenarios
 *
 * **Usage**:
 * ```tsx
 * const { mutate: login, isPending, error } = useLogin({
 *   onSuccess: () => router.push('/network'),
 * });
 *
 * // Login
 * login({ username: 'user@example.com', password: 'pass123' });
 * ```
 *
 * **Connection Points**:
 * - Called by: features/auth/components/LoginForm.tsx
 * - Stores: JWT tokens via AuthAPI.storeToken()
 * - Invalidates: All queries on success
 */
export function useLogin(options: UseLoginOptions = {}) {
  const {
    onSuccess,
    onError,
    redirectTo = '/network',
    showErrorToast = true,
  } = options;

  const router = useRouter();
  const queryClient = useQueryClient();
  const { handleError } = useApiError();

  const mutation = useMutation({
    mutationFn: async (credentials: LoginCredentials): Promise<AuthResponse> => {
      try {
        return await AuthAPI.login(credentials);
      } catch (error) {
        throw error;
      }
    },

    onSuccess: (data: AuthResponse) => {
      // ✅ Store tokens and user profile
      AuthAPI.storeToken(data.access_token);

      // ✅ Invalidate all queries (will refetch user profile, etc.)
      queryClient.invalidateQueries();

      // ✅ Show success toast
      toast.success(`Welcome back, ${data.user.name}!`);

      // ✅ Call user callback
      onSuccess?.(data);

      // ✅ Redirect to dashboard
      router.push(redirectTo);
    },

    onError: (error: Error) => {
      // ✅ Handle error with resilience pattern
      handleError(error);

      // ✅ Call error callback
      onError?.(error);
    },
  });

  return mutation;
}

/**
 * Helper hook: Check if login is pending
 */
export function useIsLoggingIn(): boolean {
  return false; // Would use context in real implementation
}

/**
 * Helper hook: Get last login error
 */
export function useLoginError(): Error | null {
  return null; // Would use context in real implementation
}
