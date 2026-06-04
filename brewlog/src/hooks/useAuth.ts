import { useCallback, useEffect, useSyncExternalStore } from "react";

import { api } from "@/lib/api";

export type CurrentUser = {
  id: string;
  email: string;
  roles: string[];
  permissions: string[];
  mfa_enabled?: boolean;
};

export type LoginResult = { mfaRequired: boolean; devMagicLink?: string | null };

type State =
  | { status: "loading" }
  | { status: "anon" }
  | { status: "auth"; user: CurrentUser };

const initialState: State = { status: "loading" };
let authState: State = initialState;
let refreshPromise: Promise<void> | null = null;
let listenersAttached = false;
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) listener();
}

function setAuthState(next: State) {
  authState = next;
  emit();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getSnapshot() {
  return authState;
}

function refreshAuth() {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const user = await api<CurrentUser>("/api/v1/auth/me");
      setAuthState({ status: "auth", user });
    } catch {
      setAuthState({ status: "anon" });
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

function ensureAuthLoaded() {
  if (authState.status !== "loading") return Promise.resolve();
  return refreshAuth();
}

function attachAuthEvents() {
  if (listenersAttached || typeof window === "undefined") return;
  listenersAttached = true;

  window.addEventListener("brewlog:session-expired", () => {
    setAuthState({ status: "anon" });
  });
  window.addEventListener("brewlog:auth-changed", () => {
    void refreshAuth();
  });
}

export function __resetAuthForTests() {
  authState = initialState;
  refreshPromise = null;
  emit();
}

export function useAuth() {
  const state = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
  const refresh = useCallback(() => refreshAuth(), []);

  useEffect(() => {
    attachAuthEvents();
    void ensureAuthLoaded();
  }, []);

  const login = useCallback(
    async (email: string, password: string): Promise<LoginResult> => {
      const result = await api<CurrentUser | { mfa_required: true; dev_magic_link?: string | null }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      if ("mfa_required" in result) return { mfaRequired: true, devMagicLink: result.dev_magic_link };
      setAuthState({ status: "auth", user: result });
      window.dispatchEvent(new CustomEvent("brewlog:auth-changed"));
      return { mfaRequired: false };
    },
    [],
  );

  const verifyMfaLogin = useCallback(
    async (totpCode: string, emailToken: string) => {
      await api<CurrentUser>("/api/v1/auth/login/verify-mfa", {
        method: "POST",
        body: JSON.stringify({ totp_code: totpCode, email_token: emailToken }),
      });
      await refresh();
      window.dispatchEvent(new CustomEvent("brewlog:auth-changed"));
    },
    [refresh],
  );

  const resendLoginEmailCode = useCallback(async () => {
    return api<{ mfa_required: true; email_sent: true; dev_magic_link?: string | null }>(
      "/api/v1/auth/login/resend-magic-link",
      { method: "POST" },
    );
  }, []);

  const register = useCallback(
    async (email: string, password: string) => {
      await api("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(async () => {
    await api("/api/v1/auth/logout", { method: "POST" });
    setAuthState({ status: "anon" });
    window.dispatchEvent(new CustomEvent("brewlog:auth-changed"));
  }, []);

  const hasPermission = useCallback(
    (code: string) =>
      state.status === "auth" && state.user.permissions.includes(code),
    [state],
  );

  return {
    state,
    user: state.status === "auth" ? state.user : null,
    permissions: state.status === "auth" ? state.user.permissions : [],
    hasPermission,
    login,
    verifyMfaLogin,
    resendLoginEmailCode,
    register,
    logout,
    refresh,
  };
}
