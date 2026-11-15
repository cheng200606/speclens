import { useState } from "react";

// 选项卡视图
const TABS = ["概览", "明细", "设置"] as const;

export function Switch1128() {
  const [active, setActive] = useState<(typeof TABS)[number]>("概览");

  return (
    <nav data-component="Switch1128">
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
export function clampSlider1129(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

export function formatSlider1129(v: number, digits = 2): string {
  return v.toFixed(digits);
}

export function scaleSlider1129(values: number[], factor: number): number[] {
  return values.map((v) => v * factor);
}

export const LIMIT3 = 36;
import { useState } from "react";

// 展示面板：受控展开/收起
type Label1130Props = { title: string; rows: string[] };

export function Label1130({ title, rows }: Label1130Props) {
  const [open, setOpen] = useState(false);

  return (
    <section data-component="Label1130">
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
