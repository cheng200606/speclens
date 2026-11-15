import { useState } from "react";

export function DeleteCard({ title }: { title: string }) {
  const [deleted, setDeleted] = useState(false);

  function remove() {
    setDeleted(true);
    void fetch("/api/cards", { method: "DELETE" });
  }

  return deleted ? null : <button onClick={remove}>Delete {title}</button>;
}
