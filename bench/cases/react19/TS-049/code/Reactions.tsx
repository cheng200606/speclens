import { useOptimistic } from "react";

export function Reactions({ likes }: { likes: number }) {
  const [optimistic, bump] = useOptimistic(likes);

  bump(1);

  return <span>{optimistic} reactions</span>;
}
