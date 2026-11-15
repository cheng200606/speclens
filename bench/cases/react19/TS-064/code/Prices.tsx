import { use } from "react";

const cache = new Map<string, Promise<unknown>>();

function getPrices(symbol: string): Promise<unknown> {
  if (!cache.has(symbol)) cache.set(symbol, fetch(`/api/prices/${symbol}`).then((r) => r.json()));
  return cache.get(symbol)!;
}

export function Prices({ symbol }: { symbol: string }) {
  const prices = use(getPrices(symbol));
  return <pre>{JSON.stringify(prices)}</pre>;
}
