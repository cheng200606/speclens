import { use } from "react";

export function Ticker({ pair }: { pair: string }) {
  const quote = use(fetch(`/api/quote/${pair}`).then((r) => r.json()));
  return <span>{quote.last}</span>;
}
