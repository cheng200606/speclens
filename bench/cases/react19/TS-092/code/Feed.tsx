import { use, Suspense } from "react";

const cache = new Map<string, Promise<{ items: unknown[] }>>();

function getFeed(cursor: string): Promise<{ items: unknown[] }> {
  if (!cache.has(cursor)) cache.set(cursor, fetch(`/api/feed?cursor=${cursor}`).then((r) => r.json()));
  return cache.get(cursor)!;
}

function List({ cursor }: { cursor: string }) {
  const data = use(getFeed(cursor));
  return <ul>{data.items.map((i, k) => <li key={k}>{String(i)}</li>)}</ul>;
}

export function Feed({ cursor }: { cursor: string }) {
  return (
    <Suspense fallback="loading">
      <List cursor={cursor} />
    </Suspense>
  );
}
