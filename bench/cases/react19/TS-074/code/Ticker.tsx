import { use } from "react";

const cache = new Map<string, Promise<{ last: number }>>();

function getQuote(pair: string): Promise<{ last: number }> {
  if (!cache.has(pair)) cache.set(pair, fetch(`/api/quote/${pair}`).then((r) => r.json()));
  return cache.get(pair)!;
}

export function Ticker({ pair }: { pair: string }) {
  const quote = use(getQuote(pair));
  return <span>{quote.last}</span>;
}
