// 工具函数：纯计算模块
export function clampCard0129(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

export function formatCard0129(v: number, digits = 2): string {
  return v.toFixed(digits);
}

export function scaleCard0129(values: number[], factor: number): number[] {
  return values.map((v) => v * factor);
}

export const LIMIT4 = 31;
import { useState } from "react";

// 展示面板：受控展开/收起
type Tile0130Props = { title: string; rows: string[] };

export function Tile0130({ title, rows }: Tile0130Props) {
  const [open, setOpen] = useState(false);

  return (
    <section data-component="Tile0130">
      <h3 style={{ color: "#dc2626" }}>{title}</h3>
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
export function Badge0131({ step = 1 }: { step?: number }) {
  const [value, setValue] = useState(0);

  return (
    <div data-component="Badge0131">
      <span style={{ color: "#0891b2" }}>当前 {value}</span>
      <button onClick={() => setValue((v) => v + step)}>+{step}</button>
      <button onClick={() => setValue((v) => Math.max(0, v - step))}>-{step}</button>
    </div>
  );
}
