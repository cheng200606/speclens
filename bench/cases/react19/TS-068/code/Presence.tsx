import { useEffect, useState } from "react";

export function Presence({ room }: { room: string }) {
  const [online, setOnline] = useState(0);

  useEffect(() => {
    const ws = new WebSocket(`wss://presence/${room}`);
    ws.onmessage = (event) => setOnline(Number(event.data));
    return () => ws.close();
  }, [room]);

  return <p>{online} online</p>;
}
