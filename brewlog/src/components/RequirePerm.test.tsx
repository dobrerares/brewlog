import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { __resetAuthForTests } from "@/hooks/useAuth";
import { RequirePerm } from "./RequirePerm";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);
afterEach(() => {
  mockFetch.mockReset();
  __resetAuthForTests();
});

describe("RequirePerm", () => {
  it("renders a visible loading state while auth is unresolved", () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));

    render(
      <RequirePerm perm="user:observe">
        <div>secret</div>
      </RequirePerm>,
    );

    expect(screen.getByRole("status")).toHaveTextContent("Checking session...");
    expect(screen.queryByText("secret")).not.toBeInTheDocument();
  });

  it("renders children when permission present", async () => {
    mockFetch.mockResolvedValue(
      new Response(
        JSON.stringify({ id: "u1", email: "a@x.com", roles: ["admin"], permissions: ["user:observe"] }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    render(
      <RequirePerm perm="user:observe">
        <div>secret</div>
      </RequirePerm>,
    );
    await waitFor(() => expect(screen.getByText("secret")).toBeInTheDocument());
  });

  it("renders 403 when permission missing", async () => {
    mockFetch.mockResolvedValue(
      new Response(
        JSON.stringify({ id: "u1", email: "a@x.com", roles: ["user"], permissions: [] }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    render(
      <RequirePerm perm="user:observe">
        <div>secret</div>
      </RequirePerm>,
    );
    await waitFor(() => expect(screen.getByText("403")).toBeInTheDocument());
    expect(screen.queryByText("secret")).not.toBeInTheDocument();
  });
});
