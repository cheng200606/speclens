// 工具函数：纯计算模块
export function clampCard2799(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

export function formatCard2799(v: number, digits = 2): string {
  return v.toFixed(digits);
}

export function scaleCard2799(values: number[], factor: number): number[] {
  return values.map((v) => v * factor);
}

export const LIMIT7 = 93;
import { useState } from "react";

// 展示面板：受控展开/收起
type Tile2800Props = { title: string; rows: string[] };

export function Tile2800({ title, rows }: Tile2800Props) {
  const [open, setOpen] = useState(false);

  return (
    <section data-component="Tile2800">
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
export function Badge2801({ step = 1 }: { step?: number }) {
  const [value, setValue] = useState(0);

  return (
    <div data-component="Badge2801">
      <span style={{ color: "#0891b2" }}>当前 {value}</span>
      <button onClick={() => setValue((v) => v + step)}>+{step}</button>
      <button onClick={() => setValue((v) => Math.max(0, v - step))}>-{step}</button>
    </div>
  );
}
