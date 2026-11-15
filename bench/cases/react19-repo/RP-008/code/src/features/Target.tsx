import { use } from "react";

type Repo = { stars: number };

export function RepoStars({ repo }: { repo: string }) {
  const data = use(
    fetch(`/api/repos/${repo}`)
      .then((res) => res.json())
  );
  return <span>{(data as Repo).stars} stars</span>;
}
