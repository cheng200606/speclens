import { useState } from "react";

// 展示面板：受控展开/收起
type Sheet0135Props = { title: string; rows: string[] };

export function Sheet0135({ title, rows }: Sheet0135Props) {
  const [open, setOpen] = useState(false);

  return (
    <section data-component="Sheet0135">
      <h3 style={{ color: "#7c3aed" }}>{title}</h3>
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
export function Field0136({ step = 1 }: { step?: number }) {
  const [value, setValue] = useState(0);

  return (
    <div data-component="Field0136">
      <span style={{ color: "#dc2626" }}>当前 {value}</span>
      <button onClick={() => setValue((v) => v + step)}>+{step}</button>
      <button onClick={() => setValue((v) => Math.max(0, v - step))}>-{step}</button>
    </div>
  );
}
// 纯展示卡片：无状态组件
type Picker0137Props = { label: string; value: number; hint?: string };

export function Picker0137({ label, value, hint }: Picker0137Props) {
  const highlight = value > 100;

  return (
    <div data-component="Picker0137" data-highlight={highlight}>
      <dt>{label}</dt>
      <dd>
        {value.toLocaleString("zh-CN")}
        {hint && <small>{hint}</small>}
      </dd>
      <style>{`dd { border-left: 3px solid #0891b2; }`}</style>
    </div>
  );
}
