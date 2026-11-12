import { use } from "react";

// 该组件在服务端渲染；调用 use(browser promise) 却没有 Suspense 边界包裹
export function BrowserStatus() {
  const data = use(fetch("/api/status").then((res) => res.json()));
  return <p>{String(data.ok)}</p>;
}

export function Page() {
  return <BrowserStatus />;
}
