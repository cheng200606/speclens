// 工具函数：纯计算模块
export function clampRow1884(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

export function formatRow1884(v: number, digits = 2): string {
  return v.toFixed(digits);
}

export function scaleRow1884(values: number[], factor: number): number[] {
  return values.map((v) => v * factor);
}

export const LIMIT2 = 45;
import { useState } from "react";

// 展示面板：受控展开/收起
type Grid1885Props = { title: string; rows: string[] };

export function Grid1885({ title, rows }: Grid1885Props) {
  const [open, setOpen] = useState(false);

  return (
    <section data-component="Grid1885">
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
export function Pane1886({ step = 1 }: { step?: number }) {
  const [value, setValue] = useState(0);

  return (
    <div data-component="Pane1886">
      <span style={{ color: "#d97706" }}>当前 {value}</span>
      <button onClick={() => setValue((v) => v + step)}>+{step}</button>
      <button onClick={() => setValue((v) => Math.max(0, v - step))}>-{step}</button>
    </div>
  );
}
