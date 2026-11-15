import { useOptimistic, startTransition } from "react";

export function ReactionPill({ count }: { count: number }) {
  const [optimistic, bump] = useOptimistic(count);

  function like() {
    startTransition(() => {
      bump((n) => n + 1);
      void fetch("/api/like", { method: "POST" });
    });
  }

  return <button onClick={like}>{optimistic}</button>;
}
