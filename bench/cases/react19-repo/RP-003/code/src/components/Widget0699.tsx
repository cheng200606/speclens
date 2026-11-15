// 纯展示卡片：无状态组件
type Modal2097Props = { label: string; value: number; hint?: string };

export function Modal2097({ label, value, hint }: Modal2097Props) {
  const highlight = value > 100;

  return (
    <div data-component="Modal2097" data-highlight={highlight}>
      <dt>{label}</dt>
      <dd>
        {value.toLocaleString("zh-CN")}
        {hint && <small>{hint}</small>}
      </dd>
      <style>{`dd { border-left: 3px solid #7c3aed; }`}</style>
    </div>
  );
}
import { useState } from "react";

// 选项卡视图
const TABS = ["概览", "明细", "设置"] as const;

export function Drawer2098() {
  const [active, setActive] = useState<(typeof TABS)[number]>("概览");

  return (
    <nav data-component="Drawer2098">
      {TABS.map((tab) => (
        <button
          key={tab}
          data-active={tab === active}
          style={{ borderColor: tab === active ? "#dc2626" : "transparent" }}
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
export function clampTooltip2099(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

export function formatTooltip2099(v: number, digits = 2): string {
  return v.toFixed(digits);
}

export function scaleTooltip2099(values: number[], factor: number): number[] {
  return values.map((v) => v * factor);
}

export const LIMIT7 = 96;
