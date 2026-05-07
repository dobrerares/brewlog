import { useObservedUsers } from "@/hooks/useObservedUsers";
import { Sparkline } from "@/components/Sparkline";

export default function ObservedUsers() {
  const { users, loading, clear } = useObservedUsers();

  return (
    <div className="mx-auto max-w-3xl p-4">
      <h1 className="mb-4 text-2xl font-semibold">Observed users</h1>
      {loading && <p>Loading…</p>}
      {!loading && users.length === 0 && (
        <p className="text-stone-500">No users currently under observation.</p>
      )}
      <ul className="space-y-3">
        {users.map((u) => (
          <li key={u.id} className="rounded border bg-white p-3">
            <div className="flex items-baseline justify-between">
              <div>
                <div className="font-mono">{u.email}</div>
                <div className="text-sm text-red-700">{u.observed_reason}</div>
                <div className="text-xs text-stone-500">
                  {u.observed_at ? new Date(u.observed_at).toLocaleString() : ""}
                </div>
              </div>
              <button
                onClick={() => clear(u.id)}
                className="rounded bg-stone-100 px-3 py-1 text-sm hover:bg-stone-200"
              >
                Clear
              </button>
            </div>
            <div className="mt-2">
              <Sparkline actions={u.recent_actions} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
