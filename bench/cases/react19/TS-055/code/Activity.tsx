import { use, Suspense } from "react";

const cache = new Map<string, Promise<unknown>>();

function getActivity(url: string): Promise<unknown> {
  if (!cache.has(url)) {
    cache.set(url, fetch(url).then((res) => res.json()));
  }
  return cache.get(url)!;
}

function Feed({ url }: { url: string }) {
  const data = use(getActivity(url));
  return <pre>{JSON.stringify(data)}</pre>;
}

export function Activity({ url }: { url: string }) {
  return (
    <Suspense fallback="loading">
      <Feed url={url} />
    </Suspense>
  );
}
