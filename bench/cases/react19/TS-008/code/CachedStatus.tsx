import { use } from "react";

const cache = new Map<string, Promise<unknown>>();

function getCachedJson(url: string): Promise<unknown> {
  let p = cache.get(url);
  if (!p) {
    p = fetch(url).then((res) => res.json());
    cache.set(url, p);
  }
  return p;
}

export function CachedStatus({ url }: { url: string }) {
  const data = use(getCachedJson(url));
  return <pre>{JSON.stringify(data)}</pre>;
}
