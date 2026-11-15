// 工具函数：纯计算模块
export function clampRow0684(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

export function formatRow0684(v: number, digits = 2): string {
  return v.toFixed(digits);
}

export function scaleRow0684(values: number[], factor: number): number[] {
  return values.map((v) => v * factor);
}

export const LIMIT6 = 60;
import { useState } from "react";

// 展示面板：受控展开/收起
type Grid0685Props = { title: string; rows: string[] };

export function Grid0685({ title, rows }: Grid0685Props) {
  const [open, setOpen] = useState(false);

  return (
    <section data-component="Grid0685">
      <h3 style={{ color: "#059669" }}>{title}</h3>
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
import { useState } from "react";

// 步进计数器
export function Pane0686({ step = 1 }: { step?: number }) {
  const [value, setValue] = useState(0);

  return (
    <div data-component="Pane0686">
      <span style={{ color: "#d97706" }}>当前 {value}</span>
      <button onClick={() => setValue((v) => v + step)}>+{step}</button>
      <button onClick={() => setValue((v) => Math.max(0, v - step))}>-{step}</button>
    </div>
  );
}
