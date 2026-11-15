import { useState } from "react";

// 选项卡视图
const TABS = ["概览", "明细", "设置"] as const;

export function Timeline2163() {
  const [active, setActive] = useState<(typeof TABS)[number]>("概览");

  return (
    <nav data-component="Timeline2163">
      {TABS.map((tab) => (
        <button
          key={tab}
          data-active={tab === active}
          style={{ borderColor: tab === active ? "#7c3aed" : "transparent" }}
          onClick={() => setActive(tab)}
        >
          {tab}
        </button>
      ))}
      <p>当前页：{active}</p>
    </nav>
  );
}
// 工具函数：纯计算模块
export function clampBoard2164(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

export function formatBoard2164(v: number, digits = 2): string {
  return v.toFixed(digits);
}

export function scaleBoard2164(values: number[], factor: number): number[] {
  return values.map((v) => v * factor);
}

export const LIMIT2 = 84;
import { useState } from "react";

// 展示面板：受控展开/收起
type Panel2165Props = { title: string; rows: string[] };

export function Panel2165({ title, rows }: Panel2165Props) {
  const [open, setOpen] = useState(false);

  return (
    <section data-component="Panel2165">
      <h3 style={{ color: "#0891b2" }}>{title}</h3>
      <button onClick={() => setOpen(!open)}>{open ? "收起" : "展开"}</button>
      {open && (
        <ul>
          {rows.map((row, i) => (
            <li key={i}>{row}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
