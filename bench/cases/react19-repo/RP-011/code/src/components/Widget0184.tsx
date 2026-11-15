// 纯展示卡片：无状态组件
type Meter0552Props = { label: string; value: number; hint?: string };

export function Meter0552({ label, value, hint }: Meter0552Props) {
  const highlight = value > 100;

  return (
    <div data-component="Meter0552" data-highlight={highlight}>
      <dt>{label}</dt>
      <dd>
        {value.toLocaleString("zh-CN")}
        {hint && <small>{hint}</small>}
      </dd>
      <style>{`dd { border-left: 3px solid #2563eb; }`}</style>
    </div>
  );
}
import { useState } from "react";

// 选项卡视图
const TABS = ["概览", "明细", "设置"] as const;

export function Tracker0553() {
  const [active, setActive] = useState<(typeof TABS)[number]>("概览");

  return (
    <nav data-component="Tracker0553">
      {TABS.map((tab) => (
        <button
          key={tab}
          data-active={tab === active}
          style={{ borderColor: tab === active ? "#059669" : "transparent" }}
          onClick={() => setActive(tab)}
        >
          {tab}
        </button>
      ))}
      <p>当前页：{active}</p>
    </nav>
  );
}
// 工具函数：纯计算模块
export function clampMarker0554(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

export function formatMarker0554(v: number, digits = 2): string {
  return v.toFixed(digits);
}

export function scaleMarker0554(values: number[], factor: number): number[] {
  return values.map((v) => v * factor);
}

export const LIMIT2 = 73;
