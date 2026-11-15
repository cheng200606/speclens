import { use } from "react";

type Row = { id: number };
const cache = new Map<string, Promise<Row[]>>();

function getRows(query: string): Promise<Row[]> {
  if (!cache.has(query)) {
    cache.set(query, fetch(`/api/rows?q=${query}`).then((r) => r.json()));
  }
  return cache.get(query)!;
}

export function Query({ query }: { query: string }) {
  const rows = use(getRows(query));
  return <ul>{rows.map((row) => <li key={row.id}>{row.id}</li>)}</ul>;
}
