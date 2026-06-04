import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { __resetAuthForTests, useAuth } from "./useAuth";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

afterEach(() => {
  mockFetch.mockReset();
  __resetAuthForTests();
});

function ok(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("useAuth", () => {
  it("loads /me on mount and exposes user", async () => {
    mockFetch.mockResolvedValue(
      ok({ id: "u1", email: "a@x.com", roles: ["user"], permissions: ["bean:read"] }),
    );
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.user?.email).toBe("a@x.com"));
    expect(result.current.hasPermission("bean:read")).toBe(true);
    expect(result.current.hasPermission("user:observe")).toBe(false);
  });

  it("falls back to anon on 401", async () => {
    mockFetch.mockResolvedValue(new Response("", { status: 401 }));
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.user).toBeNull());
  });

  it("shares a single auth check across hook consumers", async () => {
    mockFetch.mockResolvedValue(
      ok({ id: "u1", email: "a@x.com", roles: ["user"], permissions: [] }),
    );

    const first = renderHook(() => useAuth());
    const second = renderHook(() => useAuth());

    await waitFor(() => expect(first.result.current.user?.email).toBe("a@x.com"));
    await waitFor(() => expect(second.result.current.user?.email).toBe("a@x.com"));
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });
});
