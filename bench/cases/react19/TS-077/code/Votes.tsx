import { useOptimistic } from "react";

export function Votes({ total }: { total: number }) {
  const [votes, addVote] = useOptimistic(total);

  addVote(1);

  return <p>{votes} votes</p>;
}
