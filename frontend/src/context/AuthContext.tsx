'use client';

import React, { createContext, useContext, useState, useEffect, useRef, useCallback, ReactNode } from 'react';
import { User, SeedUser } from '@/lib/types';
import { api, clearSessionCsrfToken, isAuthenticationFailure } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  seedUsers: SeedUser[];
  login: (username: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  // AUTH-006 Phase 1: identity lives in memory only and is always derived
  // from the server session cookie. No token, no localStorage/sessionStorage.
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [seedUsers, setSeedUsers] = useState<SeedUser[]>([]);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const clearIdentity = useCallback(() => {
    clearSessionCsrfToken();
    setUser(null);
  }, []);

  // Load available seed personas from backend
  const loadSeedUsers = async () => {
    try {
      const data = await api.getSeedUsers();
      if (data && data.users) {
        setSeedUsers(data.users);
      }
    } catch (err) {
      console.error('Failed to load seed personas:', err);
    }
  };

  const establishSessionIdentity = useCallback(async (): Promise<User> => {
    // Session cookie authenticates; then populate the memory-only identity and
    // obtain the session-bound CSRF token for subsequent unsafe requests.
    const freshUser = await api.getMe();
    await api.getCsrfToken();
    if (mountedRef.current) {
      setUser(freshUser);
    }
    return freshUser;
  }, []);

  // Startup restoration: session cookie only, never local persistence.
  useEffect(() => {
    let cancelled = false;
    const restore = async () => {
      try {
        await loadSeedUsers();
        const freshUser = await establishSessionIdentity();
        if (!cancelled && mountedRef.current) {
          setUser(freshUser);
        }
      } catch (err) {
        if (isAuthenticationFailure(err)) {
          // No valid session: clear identity explicitly.
          if (!cancelled && mountedRef.current) {
            clearIdentity();
          }
        }
        // Transient/non-401 startup failure: keep identity unresolved (still
        // null at startup), do NOT treat it as logout. isLoading resolves so
        // the UI can retry; the next /auth/me call re-establishes state.
      } finally {
        if (!cancelled && mountedRef.current) {
          setIsLoading(false);
        }
      }
    };
    restore();
    return () => {
      cancelled = true;
    };
  }, [clearIdentity, establishSessionIdentity]);

  const login = async (username: string, password: string): Promise<User> => {
    // Cookie-setting contract: the server establishes the session and returns
    // the user profile without any access_token. The client never carries a
    // fallback/default password; the operator always supplies credentials.
    await api.login({
      username: username.trim(),
      password,
    });
    // Establish in-memory identity from the freshly set session.
    const authUser = await establishSessionIdentity();
    return authUser;
  };

  const logout = async (): Promise<void> => {
    try {
      // Backend logout is CSRF-protected and idempotent; the server clears
      // the session cookie. Clear in-memory identity only after success, or
      // when the server confirms the session is already gone (401), which the
      // existing contract treats as idempotent revocation.
      await api.logout();
      if (mountedRef.current) {
        clearIdentity();
      }
    } catch (err) {
      if (isAuthenticationFailure(err)) {
        if (mountedRef.current) {
          clearIdentity();
        }
        return;
      }
      // Retryable/server failure: do NOT claim logout succeeded.
      throw err;
    }
  };

  const refreshProfile = async () => {
    try {
      const freshUser = await api.getMe();
      if (mountedRef.current) {
        setUser(freshUser);
      }
    } catch (err) {
      if (isAuthenticationFailure(err)) {
        if (mountedRef.current) {
          clearIdentity();
        }
        return;
      }
      console.error('Failed to refresh user profile:', err);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        seedUsers,
        login,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
