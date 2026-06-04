import { useEffect, useRef } from "react";

export type IncomingFrame =
  | { type: "ready"; user_id: string }
  | { type: "history"; room_id: string; messages: Message[] }
  | { type: "message"; room_id: string; msg: Message };

export type Message = {
  id: string;
  room_id: string;
  from_user_id: string;
  body: string;
  created_at: string;
};

export function useChatSocket(onFrame: (frame: IncomingFrame) => void) {
  const ref = useRef<WebSocket | null>(null);

  useEffect(() => {
    const base = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";
    // Empty base → derive from window.location so the WS goes through Vite's
    // proxy (or the prod reverse proxy) on the same host the page came from.
    const wsUrl = base
      ? base.replace(/^http/, "ws") + "/ws"
      : `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`;
    const ws = new WebSocket(wsUrl);
    ref.current = ws;
    ws.onmessage = (e) => onFrame(JSON.parse(e.data) as IncomingFrame);
    return () => ws.close();
  }, [onFrame]);

  return {
    join: (roomId: string) => ref.current?.send(JSON.stringify({ type: "join", room_id: roomId })),
    leave: (roomId: string) => ref.current?.send(JSON.stringify({ type: "leave", room_id: roomId })),
    send: (roomId: string, body: string) =>
      ref.current?.send(JSON.stringify({ type: "send", room_id: roomId, body })),
  };
}
