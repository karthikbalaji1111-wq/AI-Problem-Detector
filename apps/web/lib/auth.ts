"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import type { User } from "./types";

const TOKEN_KEY = "nexus.access_token";
const USER_KEY = "nexus.user";

export function getStoredToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function storeSession(token: string, user?: User) {
  window.localStorage.setItem(TOKEN_KEY, token);
  if (user) {
    window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

export function clearSession() {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

export function useAuthSession() {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const urlToken = searchParams.get("token");
    if (urlToken) {
      storeSession(urlToken);
      setToken(urlToken);
      router.replace("/dashboard");
      return;
    }
    const storedToken = getStoredToken();
    const storedUser = window.localStorage.getItem(USER_KEY);
    setToken(storedToken);
    setUser(storedUser ? (JSON.parse(storedUser) as User) : null);
  }, [router, searchParams]);

  const save = useCallback((nextToken: string, nextUser: User) => {
    storeSession(nextToken, nextUser);
    setToken(nextToken);
    setUser(nextUser);
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setToken(null);
    setUser(null);
    router.push("/login");
  }, [router]);

  return { token, user, save, logout, ready: true };
}
