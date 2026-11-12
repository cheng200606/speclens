import { use } from "react";

export function Status({ url }: { url: string }) {
  // 每次渲染都新建 Promise，违反 use(promise) 的缓存要求
  const data = use(fetch(url).then((res) => res.json()));
  return <pre>{JSON.stringify(data)}</pre>;
}
