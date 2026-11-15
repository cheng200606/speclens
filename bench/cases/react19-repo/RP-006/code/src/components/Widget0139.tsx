// 纯展示卡片：无状态组件
type Modal0417Props = { label: string; value: number; hint?: string };

export function Modal0417({ label, value, hint }: Modal0417Props) {
  const highlight = value > 100;

  return (
    <div data-component="Modal0417" data-highlight={highlight}>
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

export function Drawer0418() {
  const [active, setActive] = useState<(typeof TABS)[number]>("概览");

  return (
    <nav data-component="Drawer0418">
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
export function clampTooltip0419(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

export function formatTooltip0419(v: number, digits = 2): string {
  return v.toFixed(digits);
}

export function scaleTooltip0419(values: number[], factor: number): number[] {
  return values.map((v) => v * factor);
}

export const LIMIT7 = 41;
