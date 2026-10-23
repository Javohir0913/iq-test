"use client";

// Telegram orqali kirish: veb (Login Widget) va Mini App (initData). Sessiya tokeni localStorage'da.
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { authApi, setAuthToken, type AuthUser } from "./api";
import { useTelegram } from "./telegram";

const KEY = "iq.auth";

type Status = "loading" | "guest" | "authed";

interface AuthValue {
  status: Status;
  user: AuthUser | null;
  loginWithWidget: (data: Record<string, unknown>) => Promise<void>;
  logout: () => void;
  /** Foydalanuvchi ma’lumotini serverdan qayta o‘qish (masalan, ism qulflangandan keyin) */
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthValue | null>(null);

function readToken(): string | null {
  try {
    return localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

function saveToken(token: string | null) {
  setAuthToken(token);
  try {
    if (token) localStorage.setItem(KEY, token);
    else localStorage.removeItem(KEY);
  } catch {
    /* e’tiborsiz */
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<Status>("loading");
  const [user, setUser] = useState<AuthUser | null>(null);
  const { initData } = useTelegram();

  // Saqlangan tokenni tekshirish
  useEffect(() => {
    const token = readToken();
    if (!token) {
      setStatus((s) => (s === "loading" ? "guest" : s));
      return;
    }
    setAuthToken(token);
    authApi
      .me()
      .then(({ user }) => {
        setUser(user);
        setStatus("authed");
      })
      .catch(() => {
        saveToken(null);
        setStatus("guest");
      });
  }, []);

  // Mini App ichida – avtomatik kirish
  useEffect(() => {
    if (!initData) return;
    authApi
      .webapp(initData)
      .then(({ token, user }) => {
        saveToken(token);
        setUser(user);
        setStatus("authed");
      })
      .catch(() => {});
  }, [initData]);

  const loginWithWidget = useCallback(async (data: Record<string, unknown>) => {
    const { token, user } = await authApi.widget(data);
    saveToken(token);
    setUser(user);
    setStatus("authed");
  }, []);

  const logout = useCallback(() => {
    saveToken(null);
    setUser(null);
    setStatus("guest");
  }, []);

  const refresh = useCallback(async () => {
    try {
      const { user } = await authApi.me();
      setUser(user);
    } catch {
      /* e’tiborsiz */
    }
  }, []);

  return (
    <AuthContext.Provider value={{ status, user, loginWithWidget, logout, refresh }}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
