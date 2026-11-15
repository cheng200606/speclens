import { useState } from "react";

export function Gate({ locked }: { locked: boolean }) {
  if (locked) {
    const [attempts, setAttempts] = useState(0);
    return <p>locked ({attempts})</p>;
  }
  return <p>open</p>;
}
