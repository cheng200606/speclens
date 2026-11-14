import { useState } from "react";

export function Collapsible({
  open: initialOpen,
  items,
}: {
  open: boolean | null;
  items: string[];
}) {
  // early return 之后才调用 Hook，
  // 违反“Hook 必须在所有 early return 之前调用”的要求
  if (initialOpen === null) {
    return <p>collapsed by config</p>;
  }

  const [expanded, setExpanded] = useState(initialOpen);

  return (
    <div>
      <button onClick={() => setExpanded(!expanded)}>{expanded ? "fold" : "unfold"}</button>
      {expanded && items.map((it) => <p key={it}>{it}</p>)}
    </div>
  );
}
