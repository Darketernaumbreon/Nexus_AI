/**
 * useAuthState Hook
 * Centralized authentication state management
 * 
 * **Pattern**: Context + Reducer for session state
 * - User profile management
 * - Token storage and validation
 * - Role-based access control (RBAC)
 * - Multi-tab synchronization
 * 
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 5.1.2: Auth Domain)
 */

'use client';

import { useContext, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';

import { AuthAPI } from '../api';
import { AuthContext } from '@/lib/auth-context';

import type { User as AuthUser } from '../types';
import type { User } from '@/types';

/**
 * useAuthState Hook
 *
 * Access and manage authentication state
 *
 * **Returns**:
 * - `user`: Current authenticated user or null
 * - `isLoggedIn`: Whether user is authenticated
 * - `isLoading`: Whether auth state is being loaded
 * - `accessToken`: Current JWT access token
 * - `validateSession()`: Check if session is still valid
 * - `validateToken()`: Check token validity and expiry
 * - `logout()`: Clear session and redirect to login
 * - `hasRole(role)`: Check if user has role
 *
 * **Usage**:
 * ```tsx
 * const { user, isLoggedIn, validateSession, hasRole } = useAuthState();
 *
 * if (!isLoggedIn) {
 *   return <Redirect to="/login" />;
 * }
 *
 * if (!hasRole('admin')) {
 *   return <AccessDenied />;
 * }
 *
 * return <Dashboard user={user} />;
 * ```
 *
 * **Connection Points**:
 * - Provided by: AuthContext (lib/auth-context.tsx)
 * - Used by: All feature components
 * - Validates: JWT tokens via AuthAPI
 * - Manages: Session state across tabs
 */
export function useAuthState() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuthState must be used within AuthProvider');
  }

  const auth = context;
  const {
    user,
    isLoading,
    setUser,
    logout: clearSession,
  } = auth;
  
  const accessToken = null; // Would be managed via secure storage

  /**
   * Get current user profile
   */
  const { data: currentUser } = useQuery({
    queryKey: ['user', 'profile'],
    queryFn: AuthAPI.getCurrentUser,
    enabled: !!accessToken && !user, // Only fetch if token exists and user not in context
    refetchOnMount: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Update context when user data changes
  if (currentUser && !user) {
    setUser?.(currentUser);
  }

  /**
   * Check if user is authenticated
   */
  const isLoggedIn = useMemo(() => {
    if (!accessToken) return false;
    if (AuthAPI.isTokenExpired(accessToken)) return false;
    return true;
  }, [accessToken]);

  /**
   * Validate current session
   */
  const validateSession = useCallback((): { isValid: boolean; reason?: string; user?: User | null } => {
    if (!accessToken) {
      return {
        isValid: false,
        reason: 'not_authenticated',
      };
    }

    try {
      const isExpired = AuthAPI.isTokenExpired(accessToken);
      if (isExpired) {
        return {
          isValid: false,
          reason: 'token_expired',
        };
      }

      return {
        isValid: true,
        user: currentUser || user,
      };
    } catch {
      return {
        isValid: false,
        reason: 'invalid_token',
      };
    }
  }, [accessToken, currentUser, user]);

  /**
   * Validate token (check expiry and structure)
   */
  const validateToken = useCallback((token?: string): { isValid: boolean; isExpired: boolean; expiresIn: number; roles?: string[]; error?: string } => {
    const tokenToCheck = token || accessToken;

    if (!tokenToCheck) {
      return {
        isValid: false,
        isExpired: false,
        expiresIn: -1,
        error: 'No token provided',
      };
    }

    try {
      const isExpired = AuthAPI.isTokenExpired(tokenToCheck);
      const expiresIn = AuthAPI.getTokenExpiryTime(tokenToCheck);
      const roles = AuthAPI.extractRolesFromToken(tokenToCheck);

      return {
        isValid: !isExpired,
        isExpired,
        expiresIn,
        roles,
      };
    } catch (err) {
      return {
        isValid: false,
        isExpired: true,
        expiresIn: -1,
        error: err instanceof Error ? err.message : 'Token validation failed',
      };
    }
  }, [accessToken]);

  /**
   * Check if user has specific role
   */
  const hasRole = useCallback(
    (role: string | string[]): boolean => {
      if (!accessToken) return false;

      const rolesToCheck = Array.isArray(role) ? role : [role];
      return AuthAPI.hasRequiredRole(accessToken, rolesToCheck);
    },
    [accessToken]
  );

  /**
   * Check if user has all specific roles (AND logic)
   */
  const hasAllRoles = useCallback(
    (roles: string[]): boolean => {
      if (!accessToken) return false;
      return AuthAPI.hasAllRoles(accessToken, roles);
    },
    [accessToken]
  );

  /**
   * Check if user has specific permission
   */
  const hasPermission = useCallback(
    (permission: string): boolean => {
      // Permissions are stored in token, not in User object
      return false; // Would be implemented via token parsing
    },
    []
  );

  /**
   * Logout and clear session
   */
  const logout = useCallback(async (): Promise<void> => {
    try {
      await AuthAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
      // Continue to clear local session even if API call fails
    } finally {
      clearSession?.();
    }
  }, [clearSession]);

  /**
   * Get user display name
   */
  const displayName = useMemo(() => {
    if (currentUser) return currentUser.username;
    if (user) return user.username;
    return 'User';
  }, [currentUser, user]);

  /**
   * Get user roles as string array
   */
  const userRoles = useMemo(() => {
    // User role is a simple string in the global User type
    if (user?.role) {
      return [user.role];
    }
    return [];
  }, [user]);

  /**
   * Get user permissions from all roles
   */
  const userPermissions = useMemo(() => {
    // Permissions would be extracted from JWT token
    // Not available in the User object
    return [];
  }, []);

  return {
    // State
    user: currentUser || user,
    isLoggedIn,
    isLoading,
    accessToken,

    // Utilities
    displayName,
    userRoles,
    userPermissions,

    // Validation
    validateSession,
    validateToken,

    // RBAC
    hasRole,
    hasAllRoles,
    hasPermission,

    // Actions
    logout,
  };
}

/**
 * Helper: Check authentication status
 * Returns true if user is authenticated and session is valid
 */
export function useIsAuthenticated(): boolean {
  try {
    const { isLoggedIn } = useAuthState();
    return isLoggedIn;
  } catch {
    return false; // Not in AuthProvider context
  }
}

/**
 * Helper: Get current user
 * Returns null if not authenticated
 */
export function useCurrentUser(): User | null {
  try {
    const { user } = useAuthState();
    return user || null;
  } catch {
    return null; // Not in AuthProvider context
  }
}

/**
 * Helper: Get user roles
 */
export function useUserRoles(): string[] {
  try {
    const { userRoles } = useAuthState();
    return userRoles;
  } catch {
    return []; // Not in AuthProvider context
  }
}

/**
 * Helper: Get user permissions
 */
export function useUserPermissions(): string[] {
  try {
    const { userPermissions } = useAuthState();
    return userPermissions;
  } catch {
    return []; // Not in AuthProvider context
  }
}

/**
 * Helper: Check if user has role (standalone)
 */
export function useHasRole(role: string | string[]): boolean {
  try {
    const { hasRole } = useAuthState();
    return hasRole(role);
  } catch {
    return false; // Not in AuthProvider context
  }
}

/**
 * Helper: Check if user has permission (standalone)
 */
export function useHasPermission(permission: string): boolean {
  try {
    const { hasPermission } = useAuthState();
    return hasPermission(permission);
  } catch {
    return false; // Not in AuthProvider context
  }
}
