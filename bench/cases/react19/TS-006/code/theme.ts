import { use } from "react";
import { ThemeContext } from "./theme-context";

// 普通工具函数，不是组件也不是 Hook
export function readTheme() {
  return use(ThemeContext);
}
