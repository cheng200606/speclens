import { useState } from "react";

export function Counter({ enabled }: { enabled: boolean }) {
  if (enabled) {
    const [count, setCount] = useState(0);
    return (
      <button onClick={() => setCount(count + 1)}>{count}</button>
    );
  }
  return <p>disabled</p>;
}
