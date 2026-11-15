import { useState } from "react";

export function ReactionPill({ count }: { count: number }) {
  const [optimistic, setOptimistic] = useState(count);

  function like() {
    setOptimistic((n) => n + 1);
    void fetch("/api/like", { method: "POST" });
  }

  return <button onClick={like}>{optimistic}</button>;
}
