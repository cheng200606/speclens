// 工具函数：纯计算模块
export function clampRow0714(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

export function formatRow0714(v: number, digits = 2): string {
  return v.toFixed(digits);
}

export function scaleRow0714(values: number[], factor: number): number[] {
  return values.map((v) => v * factor);
}

export const LIMIT1 = 89;
import { useState } from "react";

// 展示面板：受控展开/收起
type Grid0715Props = { title: string; rows: string[] };

export function Grid0715({ title, rows }: Grid0715Props) {
  const [open, setOpen] = useState(false);

  return (
    <section data-component="Grid0715">
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
export function Pane0716({ step = 1 }: { step?: number }) {
  const [value, setValue] = useState(0);

  return (
    <div data-component="Pane0716">
      <span style={{ color: "#d97706" }}>当前 {value}</span>
      <button onClick={() => setValue((v) => v + step)}>+{step}</button>
      <button onClick={() => setValue((v) => Math.max(0, v - step))}>-{step}</button>
    </div>
  );
}
