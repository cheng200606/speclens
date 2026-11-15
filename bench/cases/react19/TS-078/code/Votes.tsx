import { useOptimistic, startTransition } from "react";

export function Votes({ total }: { total: number }) {
  const [votes, addVote] = useOptimistic(total);

  function vote() {
    startTransition(() => {
      addVote(1);
      void fetch("/api/vote", { method: "POST" });
    });
  }

  return <button onClick={vote}>{votes} votes</button>;
}
