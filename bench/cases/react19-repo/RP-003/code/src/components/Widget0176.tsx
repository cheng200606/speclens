import { useState } from "react";

// 选项卡视图
const TABS = ["概览", "明细", "设置"] as const;

export function Switch0528() {
  const [active, setActive] = useState<(typeof TABS)[number]>("概览");

  return (
    <nav data-component="Switch0528">
      {TABS.map((tab) => (
        <button
          key={tab}
          data-active={tab === active}
          style={{ borderColor: tab === active ? "#2563eb" : "transparent" }}
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
export function clampSlider0529(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

export function formatSlider0529(v: number, digits = 2): string {
  return v.toFixed(digits);
}

export function scaleSlider0529(values: number[], factor: number): number[] {
  return values.map((v) => v * factor);
}

export const LIMIT5 = 46;
import { useState } from "react";

// 展示面板：受控展开/收起
type Label0530Props = { title: string; rows: string[] };

export function Label0530({ title, rows }: Label0530Props) {
  const [open, setOpen] = useState(false);

  return (
    <section data-component="Label0530">
      <h3 style={{ color: "#d97706" }}>{title}</h3>
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
