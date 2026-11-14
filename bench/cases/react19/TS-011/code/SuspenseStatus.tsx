import { Suspense, use } from "react";

// 模块级缓存：同一 Promise 实例跨重渲染复用（R-007 要求）
const cache = new Map<string, Promise<string>>();

function getCachedStatus(url: string): Promise<string> {
  if (!cache.has(url)) {
    cache.set(url, fetch(url).then((res) => res.json()));
  }
  return cache.get(url)!;
}

function Status({ url }: { url: string }) {
  const data = use(getCachedStatus(url));
  return <p>{String(data.ok)}</p>;
}

export function Page({ url }: { url: string }) {
  return (
    <Suspense fallback="loading">
      <Status url={url} />
    </Suspense>
  );
}
