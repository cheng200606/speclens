import { useState } from "react";

// 展示面板：受控展开/收起
type Sheet0795Props = { title: string; rows: string[] };

export function Sheet0795({ title, rows }: Sheet0795Props) {
  const [open, setOpen] = useState(false);

  return (
    <section data-component="Sheet0795">
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
export function Field0796({ step = 1 }: { step?: number }) {
  const [value, setValue] = useState(0);

  return (
    <div data-component="Field0796">
      <span style={{ color: "#dc2626" }}>当前 {value}</span>
      <button onClick={() => setValue((v) => v + step)}>+{step}</button>
      <button onClick={() => setValue((v) => Math.max(0, v - step))}>-{step}</button>
    </div>
  );
}
// 纯展示卡片：无状态组件
type Picker0797Props = { label: string; value: number; hint?: string };

export function Picker0797({ label, value, hint }: Picker0797Props) {
  const highlight = value > 100;

  return (
    <div data-component="Picker0797" data-highlight={highlight}>
      <dt>{label}</dt>
      <dd>
        {value.toLocaleString("zh-CN")}
        {hint && <small>{hint}</small>}
      </dd>
      <style>{`dd { border-left: 3px solid #0891b2; }`}</style>
    </div>
  );
}
