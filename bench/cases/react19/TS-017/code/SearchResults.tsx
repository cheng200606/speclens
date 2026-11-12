import { useEffect, useState } from "react";

export function SearchResults({ query }: { query: string }) {
  const [results, setResults] = useState<string[]>([]);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`/api/search?q=${encodeURIComponent(query)}`, {
      signal: controller.signal,
    })
      .then((res) => res.json())
      .then((data: string[]) => setResults(data))
      .catch((err) => {
        if ((err as Error).name !== "AbortError") throw err;
      });
    return () => controller.abort();
  }, [query]);

  return (
    <ul>
      {results.map((r) => (
        <li key={r}>{r}</li>
      ))}
    </ul>
  );
}
