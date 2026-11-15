import { use } from "react";

export function Stats({ slug }: { slug: string }) {
  const stats = use(fetch(`/api/stats/${slug}`).then((r) => r.json()));
  return <p>{stats.views} views</p>;
}
