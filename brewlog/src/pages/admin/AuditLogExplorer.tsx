import { useEffect, useState } from "react";

import { API_BASE } from "../../app/api/client";

type Row = {
  id: number;
  user_id: string | null;
  role_snapshot: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  status: string;
  created_at: string;
};

async function api<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`HTTP ${response.status}: ${body}`);
  }
  return (await response.json()) as T;
}

export default function AuditLogExplorer() {
  const [filterUser, setFilterUser] = useState("");
  const [filterAction, setFilterAction] = useState("");
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    const params = new URLSearchParams();
    if (filterUser) params.set("user_id", filterUser);
    if (filterAction) params.set("action", filterAction);
    params.set("page", "1");
    params.set("page_size", "100");
    try {
      const data = await api<Row[]>(`/api/v1/admin/audit-log?${params}`);
      setRows(data);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="p-4">
      <h1 className="mb-4 text-2xl font-semibold">Audit log</h1>
      <div className="mb-3 flex gap-2">
        <input
          className="rounded border p-1"
          placeholder="user id"
          value={filterUser}
          onChange={(e) => setFilterUser(e.target.value)}
        />
        <input
          className="rounded border p-1"
          placeholder="action (e.g. LOGIN_FAIL)"
          value={filterAction}
          onChange={(e) => setFilterAction(e.target.value)}
        />
        <button className="rounded bg-amber-700 px-3 text-white" onClick={load}>
          Filter
        </button>
      </div>
      {loading && <p>Loading…</p>}
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="p-1">Time</th>
            <th className="p-1">User</th>
            <th className="p-1">Role</th>
            <th className="p-1">Action</th>
            <th className="p-1">Status</th>
            <th className="p-1">Resource</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} className="border-b">
              <td className="p-1 font-mono text-xs">{new Date(r.created_at).toLocaleString()}</td>
              <td className="p-1 font-mono text-xs">{r.user_id?.slice(0, 8) ?? "—"}</td>
              <td className="p-1 text-xs">{r.role_snapshot ?? "—"}</td>
              <td className="p-1">{r.action}</td>
              <td
                className={`p-1 font-medium ${
                  r.status === "OK"
                    ? "text-green-700"
                    : r.status === "DENIED"
                    ? "text-amber-700"
                    : r.status === "FAIL"
                    ? "text-red-700"
                    : "text-stone-500"
                }`}
              >
                {r.status}
              </td>
              <td className="p-1 font-mono text-xs">
                {r.resource_type ? `${r.resource_type}/${r.resource_id?.slice(0, 8)}` : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
