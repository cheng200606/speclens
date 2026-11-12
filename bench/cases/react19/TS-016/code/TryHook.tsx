import { useState } from "react";

export function riskyParse(): number {
  throw new Error("boom");
}

export function TryHook() {
  try {
    // Hook 不得在 try/catch 块内调用
    const [value] = useState(riskyParse);
    return <p>{value}</p>;
  } catch {
    return <p>error</p>;
  }
}
