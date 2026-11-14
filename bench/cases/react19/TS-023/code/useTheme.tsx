import { use } from "react";
import { ThemeContext } from "./theme-context";

// 自定义 Hook：以 use 开头，在 Hook 顶层调用 use() 合法
export function useTheme() {
  return use(ThemeContext);
}

export function ThemeBadge() {
  const theme = useTheme();
  return <span data-theme={String(theme)}>theme</span>;
}
