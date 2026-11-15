import { useEffect, useState } from "react";

export function Reporter({ target }: { target: EventTarget }) {
  const [events, setEvents] = useState(0);

  useEffect(() => {
    const handler = () => setEvents((n) => n + 1);
    target.addEventListener("report", handler);
    return () => target.removeEventListener("report", handler);
  }, [target]);

  return <p>events: {events}</p>;
}
