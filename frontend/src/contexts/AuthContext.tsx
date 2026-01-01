"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  User,
  UserProfile,
  AuthState,
  LoginCredentials,
  RegisterData,
} from "@/types";
import { authApi, profileApi } from "@/lib/api";

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [state, setState] = useState<AuthState>({
    user: null,
    profile: null,
    isAuthenticated: false,
    isLoading: true,
  });

  // Check for existing token on mount
  useEffect(() => {
    const initAuth = async () => {
      if (typeof window === 'undefined') return;
      
      const token = localStorage.getItem("access_token");
      const savedUser = localStorage.getItem("user");
      
      if (token && savedUser) {
        try {
          const user = JSON.parse(savedUser);
          setState({
            user,
            profile: null,
            isAuthenticated: true,
            isLoading: false,
          });
          // Try to refresh profile in background
          loadUserData().catch(() => {});
        } catch {
          // Token invalid, clear it
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          localStorage.removeItem("user");
          setState((prev) => ({ ...prev, isLoading: false }));
        }
      } else {
        setState((prev) => ({ ...prev, isLoading: false }));
      }
    };

    initAuth();
  }, []);

  const loadUserData = async () => {
    try {
      const profileResponse = await profileApi.getProfile();
      const profileData = profileResponse as unknown as UserProfile;
      setState((prev) => ({
        ...prev,
        profile: profileData,
        isLoading: false,
      }));
    } catch (error) {
      console.error('Failed to load profile:', error);
    }
  };

  const login = async (credentials: LoginCredentials) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    try {
      const response = await authApi.login(credentials);
      console.log('Login response:', response);
      const data = response as unknown as { access: string; refresh: string; user: User };

      if (!data.access || !data.refresh) {
        throw new Error('Invalid login response - missing tokens');
      }

      localStorage.setItem("access_token", data.access);
      localStorage.setItem("refresh_token", data.refresh);
      localStorage.setItem("user", JSON.stringify(data.user));

      setState({
        user: data.user,
        profile: null,
        isAuthenticated: true,
        isLoading: false,
      });
      
      console.log('Auth state updated, isAuthenticated:', true);
      
      // Load profile in background
      loadUserData();
    } catch (error) {
      console.error('Login failed:', error);
      setState((prev) => ({ ...prev, isLoading: false }));
      throw error;
    }
  };

  const register = async (data: RegisterData) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    try {
      console.log('Registering with data:', data);
      await authApi.register(data);
      // After registration, login automatically using username
      await login({ username: data.username, password: data.password });
    } catch (error: any) {
      console.error('Registration error:', error.response?.data || error.message);
      setState((prev) => ({ ...prev, isLoading: false }));
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    setState({
      user: null,
      profile: null,
      isAuthenticated: false,
      isLoading: false,
    });
    router.push("/login");
  };

  const refreshProfile = async () => {
    if (state.isAuthenticated) {
      await loadUserData();
    }
  };

  const updateProfile = async (data: Partial<User>) => {
    if (state.user) {
      const updatedUser = { ...state.user, ...data };
      localStorage.setItem("user", JSON.stringify(updatedUser));
      setState((prev) => ({
        ...prev,
        user: updatedUser,
      }));
    }
  };

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        register,
        logout,
        refreshProfile,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

// HOC for protected routes
export function withAuth<P extends object>(
  WrappedComponent: React.ComponentType<P>
) {
  return function WithAuthComponent(props: P) {
    const { isAuthenticated, isLoading } = useAuth();
    const router = useRouter();

    useEffect(() => {
      if (!isLoading && !isAuthenticated) {
        router.push("/login");
      }
    }, [isAuthenticated, isLoading, router]);

    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (!isAuthenticated) {
      return null;
    }

    return <WrappedComponent {...props} />;
  };
}
