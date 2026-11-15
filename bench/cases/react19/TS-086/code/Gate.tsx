import { useState } from "react";

export function Gate({ locked }: { locked: boolean }) {
  const [attempts, setAttempts] = useState(0);

  if (locked) {
    return <p>locked ({attempts})</p>;
  }
  return <p>open</p>;
}
