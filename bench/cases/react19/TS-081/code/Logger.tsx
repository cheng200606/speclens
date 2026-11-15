import { useOptimistic, startTransition } from "react";

export function Logger({ lines }: { lines: string[] }) {
  const [optimistic, addLine] = useOptimistic(lines, (current, next: string) => {
    sessionStorage.setItem("last-line", next);
    return [...current, next];
  });

  function log() {
    startTransition(async () => {
      addLine("entry");
      await fetch("/api/log", { method: "POST" });
    });
  }

  return <button onClick={log}>{optimistic.length} lines</button>;
}
