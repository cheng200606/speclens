import { use } from "react";

declare function browserRegion(): Promise<string>;

export function GeoHint() {
  const region = use(browserRegion());
  return <span>{region}</span>;
}
