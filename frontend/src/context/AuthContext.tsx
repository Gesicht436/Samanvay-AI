'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, SeedUser, AuthTokenResponse, UserSignupRequest } from '@/lib/types';
import { api } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  seedUsers: SeedUser[];
  defaultSeedPassword: string;
  login: (username: string, password?: string) => Promise<User>;
  signup: (payload: UserSignupRequest) => Promise<User>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'samanvay_auth_token';
const USER_KEY = 'samanvay_user';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [seedUsers, setSeedUsers] = useState<SeedUser[]>([]);
  const [defaultSeedPassword, setDefaultSeedPassword] = useState<string>('Samanvay@2026');

  // Load available seed personas from backend
  const loadSeedUsers = async () => {
    try {
      const data = await api.getSeedUsers();
      if (data && data.users) {
        setSeedUsers(data.users);
        if (data.default_password) {
          setDefaultSeedPassword(data.default_password);
        }
      }
    } catch (err) {
      console.error('Failed to load seed personas:', err);
    }
  };

  // Check stored credentials on client load
  useEffect(() => {
    loadSeedUsers();

    const storedToken = localStorage.getItem(TOKEN_KEY);
    const storedUserStr = localStorage.getItem(USER_KEY);

    if (storedToken) {
      setToken(storedToken);
      if (storedUserStr) {
        try {
          setUser(JSON.parse(storedUserStr));
        } catch {
          // ignore corrupted local storage
        }
      }

      // Verify token integrity with /auth/me
      api.getMe()
        .then((freshUser) => {
          setUser(freshUser);
          localStorage.setItem(USER_KEY, JSON.stringify(freshUser));
        })
        .catch(() => {
          // Token expired or invalid
          logout();
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (username: string, password?: string): Promise<User> => {
    const pwd = password || defaultSeedPassword;
    const response: AuthTokenResponse = await api.login({
      username: username.trim(),
      password: pwd,
    });

    const authToken = response.access_token;
    const authUser = response.user;

    localStorage.setItem(TOKEN_KEY, authToken);
    localStorage.setItem(USER_KEY, JSON.stringify(authUser));

    setToken(authToken);
    setUser(authUser);
    return authUser;
  };

  const signup = async (payload: UserSignupRequest): Promise<User> => {
    const response: AuthTokenResponse = await api.signup(payload);
    const authToken = response.access_token;
    const authUser = response.user;

    localStorage.setItem(TOKEN_KEY, authToken);
    localStorage.setItem(USER_KEY, JSON.stringify(authUser));

    setToken(authToken);
    setUser(authUser);
    return authUser;
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  };

  const refreshProfile = async () => {
    try {
      const freshUser = await api.getMe();
      setUser(freshUser);
      localStorage.setItem(USER_KEY, JSON.stringify(freshUser));
    } catch (err) {
      console.error('Failed to refresh user profile:', err);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!user && !!token,
        seedUsers,
        defaultSeedPassword,
        login,
        signup,
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
