import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";

export type ObservedUser = {
  id: string;
  email: string;
  observed_reason: string | null;
  observed_at: string | null;
  recent_actions: { action: string; status: string; created_at: string }[];
};

export function useObservedUsers() {
  const [users, setUsers] = useState<ObservedUser[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setUsers(await api<ObservedUser[]>("/api/v1/admin/observed-users"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const clear = useCallback(
    async (userId: string) => {
      await api(`/api/v1/admin/observed-users/${userId}/clear`, { method: "POST" });
      await refresh();
    },
    [refresh],
  );

  return { users, loading, refresh, clear };
}
