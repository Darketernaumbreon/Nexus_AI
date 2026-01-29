/**
 * useSessionGuard Hook
 * Protects routes and components by checking authentication state
 * 
 * This hook provides:
 * - Automatic redirect to login if not authenticated
 * - Session expiry detection
 * - Token refresh on demand
 * - Loading states during auth checks
 * - Access to current user data
 * 
 * @usage
 * function ProtectedComponent() {
 *   const { user, isLoading } = useSessionGuard();
 *   
 *   if (isLoading) return <LoadingSpinner />;
 *   return <div>Welcome, {user?.username}</div>;
 * }
 */

import { useEffect, useCallback, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useContext } from 'react';
import type { User } from '@/types';

/**
 * Minimal auth context interface
 * Should match the full AuthContext from lib/auth-context.tsx
 */
interface AuthContextType {
  user: User | null;
  isLoggedIn: boolean;
  isLoading: boolean;
  setUser: (user: User | null) => void;
  logout: () => void;
}

/**
 * Session guard options
 */
interface UseSessionGuardOptions {
  required?: boolean; // Redirect to login if not authenticated
  redirectTo?: string; // Where to redirect if not authenticated (default: /login)
  checkInterval?: number; // How often to check session validity (ms)
  onSessionExpired?: () => void; // Callback when session expires
  allowedRoles?: string[]; // Only allow specific roles
}

/**
 * Hook to guard routes and components by authentication state
 * Redirects to login if user is not authenticated
 * 
 * @param options - Configuration options
 * @returns Auth state and utilities
 * 
 * @example
 * // In a protected component
 * function AdminPanel() {
 *   const { user, isLoading } = useSessionGuard({
 *     required: true,
 *     allowedRoles: ['admin']
 *   });
 *   
 *   if (isLoading) return <Spinner />;
 *   if (!user) return null; // Won't reach here due to redirect
 *   
 *   return <div>Admin Area</div>;
 * }
 */
export function useSessionGuard(options: UseSessionGuardOptions = {}) {
  const router = useRouter();
  const [isSessionValid, setIsSessionValid] = useState(true);
  const [sessionCheckLoading, setSessionCheckLoading] = useState(false);

  const {
    required = true,
    redirectTo = '/login',
    checkInterval = 5 * 60 * 1000, // 5 minutes
    onSessionExpired,
    allowedRoles,
  } = options;

  /**
   * Get auth context
   * Note: This assumes AuthProvider wraps the app
   * If using a different auth system, modify accordingly
   */
  let authContext: AuthContextType | null = null;
  try {
    // Try to use auth context if available
    // This will throw if AuthProvider is not in the component tree
    const AuthContext = require('@/lib/auth-context').AuthContext;
    authContext = useContext(AuthContext);
  } catch {
    // AuthContext not available, will handle gracefully
    authContext = null;
  }

  /**
   * Check if token is still valid (not expired)
   */
  const checkTokenValidity = useCallback(async (): Promise<boolean> => {
    try {
      setSessionCheckLoading(true);

      // Check with backend if token is still valid
      const response = await fetch('/api/v1/health/ready', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${getStoredToken()}`,
        },
      });

      if (response.status === 401) {
        // Token is invalid or expired
        return false;
      }

      return response.ok;
    } catch (error) {
      console.error('Token validity check failed:', error);
      return false;
    } finally {
      setSessionCheckLoading(false);
    }
  }, []);

  /**
   * Refresh the authentication token silently
   */
  const refreshToken = useCallback(async (): Promise<boolean> => {
    try {
      const response = await fetch('/api/v1/iam/token/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getStoredToken()}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        // Store new token (actual implementation depends on your token storage)
        storeToken(data.access_token);
        return true;
      }

      return false;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  }, []);

  /**
   * Handle session expiration
   */
  const handleSessionExpired = useCallback(async () => {
    setIsSessionValid(false);
    onSessionExpired?.();

    // Attempt silent refresh
    const refreshed = await refreshToken();

    if (!refreshed) {
      // Refresh failed, redirect to login
      router.push(redirectTo);
    }
  }, [refreshToken, router, redirectTo, onSessionExpired]);

  /**
   * Check if user has required role
   */
  const hasRequiredRole = useCallback(
    (userRole?: string): boolean => {
      if (!allowedRoles || allowedRoles.length === 0) {
        return true; // No role restriction
      }

      if (!userRole) return false;

      return allowedRoles.includes(userRole);
    },
    [allowedRoles]
  );

  /**
   * Initial authentication check
   */
  useEffect(() => {
    const checkAuth = async () => {
      // Check if token exists
      if (!getStoredToken()) {
        if (required) {
          router.push(redirectTo);
        }
        return;
      }

      // Verify token is still valid
      const isValid = await checkTokenValidity();

      if (!isValid) {
        // Try to refresh
        const refreshed = await refreshToken();

        if (!refreshed && required) {
          router.push(redirectTo);
        }
      }

      // Check role restrictions
      const userRole = authContext?.user?.role;
      if (!hasRequiredRole(userRole)) {
        router.push('/forbidden');
      }
    };

    checkAuth();
  }, [required, redirectTo, checkTokenValidity, refreshToken, router, authContext, hasRequiredRole]);

  /**
   * Setup periodic session validity checks
   */
  useEffect(() => {
    if (!getStoredToken()) return;

    const interval = setInterval(async () => {
      const isValid = await checkTokenValidity();

      if (!isValid) {
        handleSessionExpired();
      }
    }, checkInterval);

    return () => clearInterval(interval);
  }, [checkInterval, checkTokenValidity, handleSessionExpired]);

  /**
   * Listen for logout events from other tabs
   */
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'auth_token' && e.newValue === null) {
        // Token was cleared in another tab
        router.push(redirectTo);
      }
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('storage', handleStorageChange);
      return () => window.removeEventListener('storage', handleStorageChange);
    }
  }, [router, redirectTo]);

  return {
    // Auth state
    user: authContext?.user ?? null,
    isLoggedIn: authContext?.isLoggedIn ?? false,
    isLoading: authContext?.isLoading ?? false,
    isSessionValid,

    // Session checks
    checkTokenValidity,
    refreshToken,
    handleSessionExpired,
    hasRequiredRole,

    // Utils
    sessionCheckLoading,
  };
}

/**
 * Hook wrapper that requires authentication
 * Automatically redirects to login if not authenticated
 * 
 * @example
 * function SecurePage() {
 *   const { user } = useRequireAuth();
 *   return <div>Hello {user.username}</div>;
 * }
 */
export function useRequireAuth() {
  return useSessionGuard({ required: true });
}

/**
 * Hook wrapper that requires specific role
 * 
 * @example
 * function AdminPage() {
 *   const { user } = useRequireRole('admin');
 *   return <div>Admin Area</div>;
 * }
 */
export function useRequireRole(role: string | string[]) {
  const roles = Array.isArray(role) ? role : [role];
  return useSessionGuard({ required: true, allowedRoles: roles });
}

/**
 * Hook to get current user (may be null if not authenticated)
 * 
 * @example
 * function Header() {
 *   const { user, isLoading } = useCurrentUser();
 *   if (isLoading) return <Skeleton />;
 *   return user ? <span>Hi {user.username}</span> : <LoginButton />;
 * }
 */
export function useCurrentUser() {
  const guard = useSessionGuard({ required: false });
  return {
    user: guard.user,
    isLoading: guard.isLoading,
    isLoggedIn: guard.isLoggedIn,
  };
}

/**
 * Hook to manage logout
 * 
 * @example
 * function LogoutButton() {
 *   const { logout } = useLogout();
 *   return <button onClick={logout}>Logout</button>;
 * }
 */
export function useLogout() {
  const router = useRouter();

  const logout = useCallback(async () => {
    try {
      // Call logout endpoint if available
      await fetch('/api/v1/iam/logout', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${getStoredToken()}`,
        },
      }).catch(() => {
        // Logout endpoint may not exist, just clear locally
      });
    } finally {
      // Clear token and redirect
      clearStoredToken();
      router.push('/login');
    }
  }, [router]);

  return { logout };
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Token Storage Utilities
// These are placeholder implementations
// Replace with your actual token storage mechanism
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Get stored authentication token
 * Typically stored in HttpOnly cookie or localStorage
 */
function getStoredToken(): string | null {
  // This is a placeholder - in production, get from:
  // - HttpOnly cookie (most secure)
  // - localStorage (less secure)
  // - sessionStorage
  // - In-memory store

  if (typeof window === 'undefined') return null;

  try {
    // Try to get from localStorage as fallback
    return localStorage.getItem('auth_token');
  } catch {
    return null;
  }
}

/**
 * Store authentication token
 */
function storeToken(token: string): void {
  if (typeof window === 'undefined') return;

  try {
    localStorage.setItem('auth_token', token);
    // Broadcast to other tabs
    window.dispatchEvent(
      new StorageEvent('storage', {
        key: 'auth_token',
        newValue: token,
        oldValue: null,
      })
    );
  } catch (error) {
    console.error('Failed to store token:', error);
  }
}

/**
 * Clear stored authentication token
 */
function clearStoredToken(): void {
  if (typeof window === 'undefined') return;

  try {
    localStorage.removeItem('auth_token');
    // Broadcast to other tabs
    window.dispatchEvent(
      new StorageEvent('storage', {
        key: 'auth_token',
        newValue: null,
        oldValue: localStorage.getItem('auth_token'),
      })
    );
  } catch (error) {
    console.error('Failed to clear token:', error);
  }
}
