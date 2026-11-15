import { use } from "react";

const cache = new Map<string, Promise<{ views: number }>>();

function getStats(slug: string): Promise<{ views: number }> {
  if (!cache.has(slug)) cache.set(slug, fetch(`/api/stats/${slug}`).then((r) => r.json()));
  return cache.get(slug)!;
}

export function Stats({ slug }: { slug: string }) {
  const stats = use(getStats(slug));
  return <p>{stats.views} views</p>;
}
