import { useState } from "react";

// 展示面板：受控展开/收起
type Chart2640Props = { title: string; rows: string[] };

export function Chart2640({ title, rows }: Chart2640Props) {
  const [open, setOpen] = useState(false);

  return (
    <section data-component="Chart2640">
      <h3 style={{ color: "#2563eb" }}>{title}</h3>
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
export function Ledger2641({ step = 1 }: { step?: number }) {
  const [value, setValue] = useState(0);

  return (
    <div data-component="Ledger2641">
      <span style={{ color: "#059669" }}>当前 {value}</span>
      <button onClick={() => setValue((v) => v + step)}>+{step}</button>
      <button onClick={() => setValue((v) => Math.max(0, v - step))}>-{step}</button>
    </div>
  );
}
// 纯展示卡片：无状态组件
type Summary2642Props = { label: string; value: number; hint?: string };

export function Summary2642({ label, value, hint }: Summary2642Props) {
  const highlight = value > 100;

  return (
    <div data-component="Summary2642" data-highlight={highlight}>
      <dt>{label}</dt>
      <dd>
        {value.toLocaleString("zh-CN")}
        {hint && <small>{hint}</small>}
      </dd>
      <style>{`dd { border-left: 3px solid #d97706; }`}</style>
    </div>
  );
}
