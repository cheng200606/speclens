import { use, Suspense } from "react";

const cache = new Map<string, Promise<unknown>>();

function fetchStatus(url: string): Promise<unknown> {
  if (!cache.has(url)) {
    cache.set(url, fetch(url).then((res) => res.json()));
  }
  return cache.get(url)!;
}

function Status({ url }: { url: string }) {
  // use() 读取缓存 Promise，加载态交给上层 Suspense，而非 useEffect+setState 手动取数
  const data = use(fetchStatus(url));
  return <pre>{JSON.stringify(data)}</pre>;
}

export function StatusPanel({ url }: { url: string }) {
  return (
    <Suspense fallback="loading">
      <Status url={url} />
    </Suspense>
  );
}
