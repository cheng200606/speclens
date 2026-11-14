import { useContext, useState } from "react";
import { ThemeContext } from "./theme-context";

export function Toolbar({ enabled }: { enabled: boolean }) {
  // 所有 Hook 都在 early return 之前的组件顶层调用
  const [open, setOpen] = useState(false);
  const theme = useContext(ThemeContext);

  if (!enabled) {
    return <p>toolbar disabled</p>;
  }

  return (
    <button onClick={() => setOpen(!open)} data-theme={String(theme)}>
      {open ? "close" : "open"} toolbar
    </button>
  );
}
