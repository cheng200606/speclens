import { useOptimistic } from "react";

export function DeleteCard({ title }: { title: string }) {
  const [deleted, remove] = useOptimistic(false);

  function removeCard() {
    startTransition(() => {
      remove(true);
      void fetch("/api/cards", { method: "DELETE" });
    });
  }

  if (deleted) return null;
  return <button onClick={removeCard}>Delete {title}</button>;
}

import { startTransition } from "react";
