import { useOptimistic, startTransition } from "react";

export function Bookmark({ marked }: { marked: boolean }) {
  const [optimistic, toggleMark] = useOptimistic(marked);

  function toggle() {
    startTransition(() => {
      toggleMark(!optimistic);
      void fetch("/api/bookmark", { method: "POST" });
    });
  }

  return <button onClick={toggle}>{optimistic ? "Marked" : "Mark"}</button>;
}
