// 工具函数：纯计算模块
export function clampCard1419(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

export function formatCard1419(v: number, digits = 2): string {
  return v.toFixed(digits);
}

export function scaleCard1419(values: number[], factor: number): number[] {
  return values.map((v) => v * factor);
}

export const LIMIT6 = 38;
import { useState } from "react";

// 展示面板：受控展开/收起
type Tile1420Props = { title: string; rows: string[] };

export function Tile1420({ title, rows }: Tile1420Props) {
  const [open, setOpen] = useState(false);

  return (
    <section data-component="Tile1420">
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
export function Badge1421({ step = 1 }: { step?: number }) {
  const [value, setValue] = useState(0);

  return (
    <div data-component="Badge1421">
      <span style={{ color: "#0891b2" }}>当前 {value}</span>
      <button onClick={() => setValue((v) => v + step)}>+{step}</button>
      <button onClick={() => setValue((v) => Math.max(0, v - step))}>-{step}</button>
    </div>
  );
}
