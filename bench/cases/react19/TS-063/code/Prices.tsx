import { useEffect, useState } from "react";

export function Prices({ symbol }: { symbol: string }) {
  const [prices, setPrices] = useState<unknown>(null);

  useEffect(() => {
    fetch(`/api/prices/${symbol}`)
      .then((r) => r.json())
      .then(setPrices);
  }, [symbol]);

  return <pre>{JSON.stringify(prices)}</pre>;
}
