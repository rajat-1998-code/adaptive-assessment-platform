"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { ApiError } from "@/lib/api";
import { authService } from "@/services/auth/auth.service";
import type {
  AuthenticatedUser,
  LoginRequest,
  MagicLinkRequest,
  RegisterRequest,
  VerifyEmailRequest,
} from "@/types/api";

interface AuthContextValue {
  error: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  user: AuthenticatedUser | null;
  clearError: () => void;
  login: (payload: LoginRequest) => Promise<AuthenticatedUser>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<AuthenticatedUser | null>;
  register: (payload: RegisterRequest) => Promise<AuthenticatedUser>;
  requestMagicLink: (payload: MagicLinkRequest) => Promise<string>;
  resendOtp: () => Promise<string>;
  setUser: (user: AuthenticatedUser | null) => void;
  verifyEmail: (payload: VerifyEmailRequest) => Promise<AuthenticatedUser>;
  verifyMagicLink: (token: string) => Promise<AuthenticatedUser>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function toMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong. Please try again.";
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refreshUser() {
    try {
      const response = await authService.getCurrentUser();
      setUser(response.data);
      setError(null);
      return response.data;
    } catch (error) {
      if (error instanceof ApiError && error.statusCode === 401) {
        try {
          const refreshResponse = await authService.refresh();
          setUser(refreshResponse.data);
          setError(null);
          return refreshResponse.data;
        } catch {
          setUser(null);
          return null;
        }
      }

      setError(toMessage(error));
      setUser(null);
      return null;
    }
  }

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      try {
        const currentUser = await refreshUser();
        if (!active) {
          return;
        }
        setUser(currentUser);
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    void bootstrap();

    return () => {
      active = false;
    };
  }, []);

  async function login(payload: LoginRequest) {
    try {
      const response = await authService.login(payload);
      setUser(response.data);
      setError(null);
      return response.data;
    } catch (error) {
      const message = toMessage(error);
      setError(message);
      throw error;
    }
  }

  async function register(payload: RegisterRequest) {
    try {
      const response = await authService.register(payload);
      setUser(response.data);
      setError(null);
      return response.data;
    } catch (error) {
      const message = toMessage(error);
      setError(message);
      throw error;
    }
  }

  async function logout() {
    try {
      await authService.logout();
    } finally {
      setUser(null);
      setError(null);
    }
  }

  async function resendOtp() {
    try {
      const response = await authService.resendOtp();
      setError(null);
      return response.data.message;
    } catch (error) {
      const message = toMessage(error);
      setError(message);
      throw error;
    }
  }

  async function verifyEmail(payload: VerifyEmailRequest) {
    try {
      const response = await authService.verifyEmail(payload);
      setUser(response.data);
      setError(null);
      return response.data;
    } catch (error) {
      const message = toMessage(error);
      setError(message);
      throw error;
    }
  }

  async function requestMagicLink(payload: MagicLinkRequest) {
    try {
      const response = await authService.requestMagicLink(payload);
      setError(null);
      return response.data.message;
    } catch (error) {
      const message = toMessage(error);
      setError(message);
      throw error;
    }
  }

  async function verifyMagicLink(token: string) {
    try {
      const response = await authService.verifyMagicLink(token);
      setUser(response.data);
      setError(null);
      return response.data;
    } catch (error) {
      const message = toMessage(error);
      setError(message);
      throw error;
    }
  }

  function clearError() {
    setError(null);
  }

  return (
    <AuthContext.Provider
      value={{
        error,
        isAuthenticated: user !== null,
        isLoading,
        user,
        clearError,
        login,
        logout,
        refreshUser,
        register,
        requestMagicLink,
        resendOtp,
        setUser,
        verifyEmail,
        verifyMagicLink,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
}
