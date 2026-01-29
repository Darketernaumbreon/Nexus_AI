/**
 * Authentication API
 * Handles all auth-related API calls
 * 
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 5.1.2: Auth Domain)
 */

import type { AuthResponse, LoginCredentials, User } from './types';
import { setToken, getToken, clearToken } from '@/lib/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * ============================================
 * Token Management
 * ============================================
 */

/**
 * Store JWT token in secure storage (httpOnly cookie in production)
 */
export function storeToken(token: string): void {
  setToken(token);
  // In production, this would set httpOnly cookie via backend
  if (typeof window !== 'undefined') {
    sessionStorage.setItem('nexus_access_token', token);
  }
}

/**
 * Retrieve stored JWT token
 */
export function retrieveToken(): string | null {
  if (typeof window !== 'undefined') {
    return sessionStorage.getItem('nexus_access_token') || getToken();
  }
  return getToken();
}

/**
 * Clear JWT token from storage
 */
export function removeToken(): void {
  clearToken();
  if (typeof window !== 'undefined') {
    sessionStorage.removeItem('nexus_access_token');
  }
}

/**
 * ============================================
 * Authentication Endpoints
 * ============================================
 */

/**
 * POST /iam/login/access-token
 * User login with credentials
 * 
 * @param credentials - Username and password
 * @returns AuthResponse with JWT token
 * @throws Error on invalid credentials (401)
 */
export async function login(credentials: LoginCredentials): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/iam/login/access-token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username: credentials.username,
      password: credentials.password,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Login failed' }));
    throw new Error(error.message || `Login failed with status ${response.status}`);
  }

  const data: AuthResponse = await response.json();
  
  // Store token immediately on successful login
  storeToken(data.access_token);
  
  return data;
}

/**
 * POST /iam/token/refresh
 * Silent token refresh (called before token expires)
 * 
 * @param refreshToken - Refresh token from initial login
 * @returns New AuthResponse with refreshed JWT
 * @throws Error if refresh fails (401 if refresh token expired)
 */
export async function refreshToken(refreshToken: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/iam/token/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      refresh_token: refreshToken,
    }),
  });

  if (!response.ok) {
    // 401 means refresh token expired, need to re-login
    if (response.status === 401) {
      removeToken();
      throw new Error('Session expired. Please login again.');
    }
    throw new Error(`Token refresh failed with status ${response.status}`);
  }

  const data: AuthResponse = await response.json();
  
  // Store new token
  storeToken(data.access_token);
  
  return data;
}

/**
 * GET /iam/user/profile
 * Get current user profile
 * 
 * @returns User profile data
 * @throws Error if request fails or user not authenticated (401)
 */
export async function getCurrentUser(): Promise<User> {
  const token = retrieveToken();
  
  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${API_BASE_URL}/iam/user/profile`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      removeToken();
      throw new Error('Session expired');
    }
    throw new Error(`Failed to get user profile: ${response.status}`);
  }

  return response.json();
}

/**
 * POST /iam/logout
 * Logout user and invalidate token on backend
 * 
 * @throws Error if logout fails
 */
export async function logout(): Promise<void> {
  const token = retrieveToken();
  
  if (!token) {
    // No token, just clear local storage
    removeToken();
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/iam/logout`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok && response.status !== 401) {
      throw new Error(`Logout failed with status ${response.status}`);
    }
  } catch (error) {
    console.error('Logout error:', error);
    // Continue to clear local token even if server call fails
  } finally {
    removeToken();
  }
}

/**
 * ============================================
 * JWT Token Validation
 * ============================================
 */

/**
 * Decode JWT payload (without verification, for client-side checks)
 * 
 * @param token - JWT token
 * @returns Decoded payload
 */
export function decodeJWT(token: string): Record<string, any> {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      throw new Error('Invalid token format');
    }

    // Decode payload (second part)
    const payload = parts[1];
    const decoded = JSON.parse(
      Buffer.from(payload, 'base64').toString('utf-8')
    );

    return decoded;
  } catch (error) {
    console.error('JWT decode error:', error);
    return {};
  }
}

/**
 * Check if JWT token is expired
 * 
 * @param token - JWT token
 * @returns true if expired, false otherwise
 */
export function isTokenExpired(token: string): boolean {
  try {
    const decoded = decodeJWT(token);
    if (!decoded.exp) {
      return false; // No expiry, assume valid
    }

    // exp is in seconds, Date.now() is in milliseconds
    const expiryTime = decoded.exp * 1000;
    return Date.now() >= expiryTime;
  } catch {
    return true; // Assume expired if can't decode
  }
}

/**
 * Get time remaining before token expires (in seconds)
 * 
 * @param token - JWT token
 * @returns Seconds until expiry, or -1 if already expired
 */
export function getTokenExpiryTime(token: string): number {
  try {
    const decoded = decodeJWT(token);
    if (!decoded.exp) {
      return Infinity; // No expiry
    }

    const expiryTime = decoded.exp * 1000;
    const timeRemaining = Math.floor((expiryTime - Date.now()) / 1000);
    
    return timeRemaining > 0 ? timeRemaining : -1;
  } catch {
    return -1;
  }
}

/**
 * Extract user roles from JWT token
 * 
 * @param token - JWT token
 * @returns Array of role strings
 */
export function extractRolesFromToken(token: string): string[] {
  try {
    const decoded = decodeJWT(token);
    return decoded.roles || decoded.scopes || [];
  } catch {
    return [];
  }
}

/**
 * ============================================
 * Role-Based Access Control
 * ============================================
 */

/**
 * Check if user has required role
 * 
 * @param token - JWT token
 * @param requiredRoles - Single role or array of roles (OR logic)
 * @returns true if user has any of the required roles
 */
export function hasRequiredRole(token: string, requiredRoles: string | string[]): boolean {
  const roles = extractRolesFromToken(token);
  const requiredArray = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];
  
  return requiredArray.some(role => roles.includes(role));
}

/**
 * Check if user has ALL required roles
 * 
 * @param token - JWT token
 * @param requiredRoles - Array of roles (AND logic)
 * @returns true if user has all required roles
 */
export function hasAllRoles(token: string, requiredRoles: string[]): boolean {
  const roles = extractRolesFromToken(token);
  return requiredRoles.every(role => roles.includes(role));
}

export const AuthAPI = {
  login,
  refreshToken,
  getCurrentUser,
  logout,
  decodeJWT,
  isTokenExpired,
  getTokenExpiryTime,
  extractRolesFromToken,
  hasRequiredRole,
  hasAllRoles,
  storeToken,
  retrieveToken,
  removeToken,
};
