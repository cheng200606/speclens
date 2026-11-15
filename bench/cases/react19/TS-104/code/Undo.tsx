import { useOptimistic, startTransition } from "react";

export function Undo({ entries }: { entries: string[] }) {
  const [list, push] = useOptimistic(entries, (current, next: string) => [...current, next]);

  function add() {
    startTransition(() => push("item"));
  }

  return <button onClick={add}>{list.length} entries</button>;
}
