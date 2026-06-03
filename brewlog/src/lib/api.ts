// Empty default = relative URLs → routed through Vite's dev-server proxy
// (or behind a reverse proxy in prod). Override only when calling a remote
// backend directly from the browser (which then needs CORS + SameSite=None).
const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

export async function api<T = unknown>(
  path: string,
  init: RequestInit = {},
  retry = true,
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });
  const canRefresh = path !== "/api/v1/auth/refresh" && path !== "/api/v1/auth/login/verify-mfa";
  if (res.status === 401 && retry && canRefresh) {
    const refreshed = await fetch(`${BASE}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    });
    if (refreshed.ok) return api<T>(path, init, false);
    window.dispatchEvent(new CustomEvent("brewlog:session-expired"));
  }
  if (!res.ok) {
    const body = await res.text();
    const err = new Error(body || res.statusText) as Error & { status: number };
    err.status = res.status;
    throw err;
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
