import { use, Suspense } from "react";

declare function browserRegion(): Promise<string>;

function Region() {
  const region = use(browserRegion());
  return <span>{region}</span>;
}

export function GeoHint() {
  return (
    <Suspense fallback="...">
      <Region />
    </Suspense>
  );
}
