import { useCallback, useEffect, useState } from "react";

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

export function useAuth() {
  const [state, setState] = useState<State>({ status: "loading" });

  const refresh = useCallback(async () => {
    try {
      const user = await api<CurrentUser>("/api/v1/auth/me");
      setState({ status: "auth", user });
    } catch {
      setState({ status: "anon" });
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    const expire = () => setState({ status: "anon" });
    const changed = () => refresh();
    window.addEventListener("brewlog:session-expired", expire);
    window.addEventListener("brewlog:auth-changed", changed);
    return () => {
      window.removeEventListener("brewlog:session-expired", expire);
      window.removeEventListener("brewlog:auth-changed", changed);
    };
  }, [refresh]);

  const login = useCallback(
    async (email: string, password: string): Promise<LoginResult> => {
      const result = await api<CurrentUser | { mfa_required: true; dev_magic_link?: string | null }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      if ("mfa_required" in result) return { mfaRequired: true, devMagicLink: result.dev_magic_link };
      await refresh();
      window.dispatchEvent(new CustomEvent("brewlog:auth-changed"));
      return { mfaRequired: false };
    },
    [refresh],
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
    setState({ status: "anon" });
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
