import { useEffect, useState } from "react";

export function ServicePoller({ endpoint }: { endpoint: string }) {
  const [hits, setHits] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      fetch(endpoint)
        .then((res) => res.json())
        .then(() => setHits((n) => n + 1));
    }, 5000);
    console.log("polling started for", endpoint, id);
  }, [endpoint]);

  return <p>poll hits: {hits}</p>;
}
