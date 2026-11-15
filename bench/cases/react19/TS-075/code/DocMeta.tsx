import { use } from "react";

type Meta = { title: string };

export function DocMeta({ metaPromise }: { metaPromise: Promise<Meta> & { status?: string } }) {
  if (metaPromise.status !== "fulfilled") {
    return <p>pending</p>;
  }
  const meta = use(metaPromise);
  return <h2>{meta.title}</h2>;
}
