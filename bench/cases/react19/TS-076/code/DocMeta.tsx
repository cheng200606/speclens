import { use, Suspense } from "react";

type Meta = { title: string };

function Title({ metaPromise }: { metaPromise: Promise<Meta> }) {
  const meta = use(metaPromise);
  return <h2>{meta.title}</h2>;
}

export function DocMeta({ metaPromise }: { metaPromise: Promise<Meta> }) {
  return (
    <Suspense fallback="pending">
      <Title metaPromise={metaPromise} />
    </Suspense>
  );
}
