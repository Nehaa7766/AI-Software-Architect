"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { authApi, type User } from "@/features/auth/api/auth.api";
import { setAccessToken } from "@/lib/axios";

/** Readable cookie flag so Next.js middleware can gate routes at the edge. */
const AUTH_FLAG = "aisa_auth";
function setAuthFlag(on: boolean) {
  if (typeof document === "undefined") return;
  document.cookie = on
    ? `${AUTH_FLAG}=1; path=/; max-age=604800; samesite=lax`
    : `${AUTH_FLAG}=; path=/; max-age=0; samesite=lax`;
}

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  loginWithGoogle: (idToken: string) => Promise<void>;
  register: (data: {
    firstName: string;
    lastName: string;
    email: string;
    password: string;
    confirmPassword: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const applySession = (accessToken: string, nextUser: User) => {
    setAccessToken(accessToken);
    setUser(nextUser);
    setAuthFlag(true);
  };

  const clearSession = () => {
    setAccessToken(null);
    setUser(null);
    setAuthFlag(false);
  };

  // Bootstrap: silently refresh, then load the current user.
  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const res = await authApi.refresh();
        if (!active) return;
        applySession(res.access_token, res.user);
      } catch {
        if (active) clearSession();
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const login = async (email: string, password: string, rememberMe = false) => {
    const res = await authApi.login({ email, password, remember_me: rememberMe });
    applySession(res.access_token, res.user);
  };

  const loginWithGoogle = async (idToken: string) => {
    const res = await authApi.google(idToken);
    applySession(res.access_token, res.user);
  };

  const register: AuthContextValue["register"] = async (data) => {
    const res = await authApi.register({
      first_name: data.firstName,
      last_name: data.lastName,
      email: data.email,
      password: data.password,
      confirm_password: data.confirmPassword,
    });
    applySession(res.access_token, res.user);
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      clearSession();
    }
  };

  const refreshUser = async () => {
    const me = await authApi.me();
    setUser(me);
  };

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      isAuthenticated: !!user,
      login,
      loginWithGoogle,
      register,
      logout,
      refreshUser,
    }),
    // Action closures capture only stable setState setters; recompute on state.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuthContext must be used within <AuthProvider>");
  return ctx;
}
