import { useState } from "react";

// 展示面板：受控展开/收起
type Chart2670Props = { title: string; rows: string[] };

export function Chart2670({ title, rows }: Chart2670Props) {
  const [open, setOpen] = useState(false);

  return (
    <section data-component="Chart2670">
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
export function Ledger2671({ step = 1 }: { step?: number }) {
  const [value, setValue] = useState(0);

  return (
    <div data-component="Ledger2671">
      <span style={{ color: "#059669" }}>当前 {value}</span>
      <button onClick={() => setValue((v) => v + step)}>+{step}</button>
      <button onClick={() => setValue((v) => Math.max(0, v - step))}>-{step}</button>
    </div>
  );
}
// 纯展示卡片：无状态组件
type Summary2672Props = { label: string; value: number; hint?: string };

export function Summary2672({ label, value, hint }: Summary2672Props) {
  const highlight = value > 100;

  return (
    <div data-component="Summary2672" data-highlight={highlight}>
      <dt>{label}</dt>
      <dd>
        {value.toLocaleString("zh-CN")}
        {hint && <small>{hint}</small>}
      </dd>
      <style>{`dd { border-left: 3px solid #d97706; }`}</style>
    </div>
  );
}
