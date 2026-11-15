import { useState } from "react";

export function Bookmark({ marked }: { marked: boolean }) {
  const [state, setState] = useState(marked);

  function toggle() {
    setState(!state);
    void fetch("/api/bookmark", { method: "POST" });
  }

  return <button onClick={toggle}>{state ? "Marked" : "Mark"}</button>;
}
