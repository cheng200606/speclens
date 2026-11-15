import { useEffect, useState } from "react";

export function Feed({ cursor }: { cursor: string }) {
  const [items, setItems] = useState<unknown[]>([]);

  useEffect(() => {
    fetch(`/api/feed?cursor=${cursor}`)
      .then((r) => r.json())
      .then((d) => setItems(d.items));
  }, [cursor]);

  return <ul>{items.map((i, k) => <li key={k}>{String(i)}</li>)}</ul>;
}
