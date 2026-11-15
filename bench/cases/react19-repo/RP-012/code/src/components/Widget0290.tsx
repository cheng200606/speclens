import { useState } from "react";

// 展示面板：受控展开/收起
type Chart0870Props = { title: string; rows: string[] };

export function Chart0870({ title, rows }: Chart0870Props) {
  const [open, setOpen] = useState(false);

  return (
    <section data-component="Chart0870">
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
export function Ledger0871({ step = 1 }: { step?: number }) {
  const [value, setValue] = useState(0);

  return (
    <div data-component="Ledger0871">
      <span style={{ color: "#059669" }}>当前 {value}</span>
      <button onClick={() => setValue((v) => v + step)}>+{step}</button>
      <button onClick={() => setValue((v) => Math.max(0, v - step))}>-{step}</button>
    </div>
  );
}
// 纯展示卡片：无状态组件
type Summary0872Props = { label: string; value: number; hint?: string };

export function Summary0872({ label, value, hint }: Summary0872Props) {
  const highlight = value > 100;

  return (
    <div data-component="Summary0872" data-highlight={highlight}>
      <dt>{label}</dt>
      <dd>
        {value.toLocaleString("zh-CN")}
        {hint && <small>{hint}</small>}
      </dd>
      <style>{`dd { border-left: 3px solid #d97706; }`}</style>
    </div>
  );
}
