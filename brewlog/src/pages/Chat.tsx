import { useCallback, useEffect, useState } from "react";

import { AuthLoading } from "@/components/AuthLoading";
import { useAuth } from "@/hooks/useAuth";
import { useChatRooms, type Room } from "@/hooks/useChatRooms";
import { useChatSocket, type IncomingFrame, type Message } from "@/hooks/useChatSocket";

export default function Chat() {
  const { state, user } = useAuth();
  const { rooms } = useChatRooms();
  const [active, setActive] = useState<Room | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");

  const onFrame = useCallback((frame: IncomingFrame) => {
    if (frame.type === "history") {
      setMessages(frame.messages.slice().reverse());
    } else if (frame.type === "message" && active && frame.room_id === active.id) {
      setMessages((prev) => [...prev, frame.msg]);
    }
  }, [active]);

  const ws = useChatSocket(onFrame);

  useEffect(() => {
    if (!active) return;
    ws.join(active.id);
    return () => ws.leave(active.id);
  }, [active, ws]);

  if (state.status === "loading") return <AuthLoading />;
  if (!user) return <AuthLoading message="Sign in to use chat." />;
  return (
    <div className="grid grid-cols-[200px_1fr] gap-4 p-4">
      <aside className="space-y-1">
        <h2 className="text-sm font-semibold uppercase text-stone-500">Rooms</h2>
        {rooms.map((r) => (
          <button
            key={r.id}
            onClick={() => {
              setMessages([]);
              setActive(r);
            }}
            className={`block w-full rounded p-2 text-left ${
              active?.id === r.id ? "bg-amber-100" : "hover:bg-stone-100"
            }`}
          >
            {r.name ?? r.participants.find((p) => p !== user.id) ?? "DM"}
          </button>
        ))}
      </aside>
      <main className="flex flex-col">
        <div className="flex-1 overflow-y-auto space-y-1 p-2">
          {messages.map((m) => (
            <div key={m.id} className="text-sm">
              <span className="font-mono text-stone-500">{m.from_user_id.slice(0, 8)}:</span>{" "}
              {m.body}
            </div>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!active || !draft.trim()) return;
            ws.send(active.id, draft);
            setDraft("");
          }}
          className="flex gap-2 border-t pt-2"
        >
          <input
            className="flex-1 rounded border p-2"
            placeholder="message…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            disabled={!active}
          />
          <button
            className="rounded bg-amber-700 px-4 text-white disabled:opacity-50"
            type="submit"
            disabled={!active}
          >
            Send
          </button>
        </form>
      </main>
    </div>
  );
}
