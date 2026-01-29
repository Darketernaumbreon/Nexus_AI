/**
 * Authentication Types
 * Type definitions for auth domain
 * 
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 5.1.2: Auth Domain)
 */

/**
 * User credentials for login
 */
export interface LoginCredentials {
  username: string;
  password: string;
}

/**
 * JWT Token payload structure
 */
export interface JWTPayload {
  /** Subject (user ID) */
  sub: string;
  
  /** Issued at (timestamp in seconds) */
  iat: number;
  
  /** Expiration time (timestamp in seconds) */
  exp: number;
  
  /** User roles/scopes */
  roles?: string[];
  scopes?: string[];
  
  /** User email */
  email?: string;
  
  /** Additional claims */
  [key: string]: any;
}

/**
 * Authentication response from login/refresh endpoints
 */
export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'Bearer';
  expires_in: number; // seconds
  user: User;
}

/**
 * User profile data
 */
export interface User {
  /** User ID */
  id: string;
  
  /** Username */
  username: string;
  
  /** Email address */
  email: string;
  
  /** Display name */
  name: string;
  
  /** User roles */
  roles: UserRole[];
  
  /** Account status */
  is_active: boolean;
  
  /** Account creation timestamp */
  created_at: string;
  
  /** Last login timestamp */
  last_login?: string;
  
  /** Additional metadata */
  metadata?: Record<string, any>;
}

/**
 * User role with permissions
 */
export interface UserRole {
  /** Role ID */
  id: string;
  
  /** Role name (e.g., 'admin', 'analyst', 'viewer') */
  name: string;
  
  /** Role permissions */
  permissions: string[];
  
  /** Role description */
  description?: string;
}

/**
 * Session state in context/store
 */
export interface SessionState {
  /** Current authenticated user */
  user: User | null;
  
  /** JWT access token */
  accessToken: string | null;
  
  /** Refresh token */
  refreshToken: string | null;
  
  /** Whether session is being loaded */
  isLoading: boolean;
  
  /** Authentication error message */
  error: string | null;
  
  /** Whether user is authenticated */
  isAuthenticated: boolean;
}

/**
 * Options for useSessionGuard hook
 */
export interface UseSessionGuardOptions {
  /** Redirect path when not authenticated (default: '/login') */
  redirectTo?: string;
  
  /** Callback when session expires */
  onSessionExpired?: () => void;
  
  /** Callback when authentication fails */
  onAuthError?: (error: Error) => void;
  
  /** Enable auto token refresh (default: true) */
  autoRefresh?: boolean;
  
  /** Token refresh interval in seconds (default: 300 = 5 minutes) */
  refreshInterval?: number;
}

/**
 * Login response from useLogin mutation
 */
export interface LoginResponse {
  success: boolean;
  user?: User;
  error?: string;
}

/**
 * Role-based access control options
 */
export interface RBACOptions {
  /** Required roles (OR logic - user needs at least one) */
  requiredRoles?: string[];
  
  /** All required roles (AND logic - user needs all) */
  allRequiredRoles?: string[];
  
  /** Fallback component to show if access denied */
  fallback?: React.ReactNode;
}

/**
 * Permission checking options
 */
export interface PermissionCheckOptions {
  /** Required permissions */
  required: string[];
  
  /** Use AND logic (all required) or OR logic (any required) */
  logic?: 'AND' | 'OR';
}

/**
 * Token validation result
 */
export interface TokenValidationResult {
  /** Token is valid */
  isValid: boolean;
  
  /** Token is expired */
  isExpired: boolean;
  
  /** Seconds until expiry (-1 if expired) */
  expiresIn: number;
  
  /** User ID from token */
  userId?: string;
  
  /** User roles from token */
  roles?: string[];
  
  /** Validation error message */
  error?: string;
}

/**
 * Session validation result
 */
export interface SessionValidationResult {
  /** Session is valid and active */
  isValid: boolean;
  
  /** Reason if invalid */
  reason?: 'token_expired' | 'not_authenticated' | 'invalid_token' | 'unknown';
  
  /** Current user (if valid) */
  user?: User;
}
