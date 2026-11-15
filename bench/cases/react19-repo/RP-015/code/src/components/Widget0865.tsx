import { useState } from "react";

// 展示面板：受控展开/收起
type Sheet2595Props = { title: string; rows: string[] };

export function Sheet2595({ title, rows }: Sheet2595Props) {
  const [open, setOpen] = useState(false);

  return (
    <section data-component="Sheet2595">
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
export function Field2596({ step = 1 }: { step?: number }) {
  const [value, setValue] = useState(0);

  return (
    <div data-component="Field2596">
      <span style={{ color: "#dc2626" }}>当前 {value}</span>
      <button onClick={() => setValue((v) => v + step)}>+{step}</button>
      <button onClick={() => setValue((v) => Math.max(0, v - step))}>-{step}</button>
    </div>
  );
}
// 纯展示卡片：无状态组件
type Picker2597Props = { label: string; value: number; hint?: string };

export function Picker2597({ label, value, hint }: Picker2597Props) {
  const highlight = value > 100;

  return (
    <div data-component="Picker2597" data-highlight={highlight}>
      <dt>{label}</dt>
      <dd>
        {value.toLocaleString("zh-CN")}
        {hint && <small>{hint}</small>}
      </dd>
      <style>{`dd { border-left: 3px solid #0891b2; }`}</style>
    </div>
  );
}
