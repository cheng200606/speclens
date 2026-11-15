import { useOptimistic, startTransition } from "react";

import { MAX_ITEMS } from "./config";

export function Undo({ entries }: { entries: string[] }) {
  const [list, push] = useOptimistic(entries, (current, next: string) => {
    if (current.length >= MAX_ITEMS) return current;
    return [...current, next];
  });

  function add() {
    startTransition(() => push("item"));
  }

  return <button onClick={add}>{list.length} entries</button>;
}
