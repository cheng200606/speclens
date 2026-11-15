import { use } from "react";

type Repo = { stars: number };
const cache = new Map<string, Promise<Repo>>();

function getCachedRepo(repo: string): Promise<Repo> {
  if (!cache.has(repo)) {
    cache.set(
      repo,
      fetch(`/api/repos/${repo}`).then((res) => res.json())
    );
  }
  return cache.get(repo)!;
}

export function RepoStars({ repo }: { repo: string }) {
  const data = use(getCachedRepo(repo));
  return <span>{data.stars} stars</span>;
}
