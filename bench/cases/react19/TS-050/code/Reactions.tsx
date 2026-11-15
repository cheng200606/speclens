import { useOptimistic, startTransition } from "react";

export function Reactions({ likes }: { likes: number }) {
  const [optimistic, bump] = useOptimistic(likes);

  return (
    <button
      onClick={() =>
        startTransition(() => {
          bump(1);
        })
      }
    >
      {optimistic} reactions
    </button>
  );
}
