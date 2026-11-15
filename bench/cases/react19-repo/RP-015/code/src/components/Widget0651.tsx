import { useState } from "react";

// 选项卡视图
const TABS = ["概览", "明细", "设置"] as const;

export function Timeline1953() {
  const [active, setActive] = useState<(typeof TABS)[number]>("概览");

  return (
    <nav data-component="Timeline1953">
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
export function clampBoard1954(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

export function formatBoard1954(v: number, digits = 2): string {
  return v.toFixed(digits);
}

export function scaleBoard1954(values: number[], factor: number): number[] {
  return values.map((v) => v * factor);
}

export const LIMIT2 = 48;
import { useState } from "react";

// 展示面板：受控展开/收起
type Panel1955Props = { title: string; rows: string[] };

export function Panel1955({ title, rows }: Panel1955Props) {
  const [open, setOpen] = useState(false);

  return (
    <section data-component="Panel1955">
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
