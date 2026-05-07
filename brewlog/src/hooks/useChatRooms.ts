import { useEffect, useState } from "react";

import { api } from "@/lib/api";

export type Room = {
  id: string;
  type: "dm" | "room";
  name: string | null;
  participants: string[];
  last_message_at: string | null;
};

export function useChatRooms() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<Room[]>("/api/v1/chat/rooms")
      .then(setRooms)
      .finally(() => setLoading(false));
  }, []);

  async function startDm(participantId: string) {
    const room = await api<Room>("/api/v1/chat/rooms", {
      method: "POST",
      body: JSON.stringify({ participant_id: participantId }),
    });
    setRooms((prev) => (prev.find((r) => r.id === room.id) ? prev : [...prev, room]));
    return room;
  }

  return { rooms, loading, startDm };
}
