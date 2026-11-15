import { useEffect, useState } from "react";

export function ServicePoller({ endpoint }: { endpoint: string }) {
  const [hits, setHits] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      fetch(endpoint)
        .then((res) => res.json())
        .then(() => setHits((n) => n + 1));
    }, 5000);
    const onOnline = () => setHits((n) => n + 1);
    window.addEventListener("online", onOnline);
    return () => {
      clearInterval(id);
      window.removeEventListener("online", onOnline);
    };
  }, [endpoint]);

  return <p>poll hits: {hits}</p>;
}
