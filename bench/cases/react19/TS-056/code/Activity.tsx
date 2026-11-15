import { useEffect, useState } from "react";

export function Activity({ url }: { url: string }) {
  const [data, setData] = useState<unknown>(null);

  useEffect(() => {
    fetch(url)
      .then((res) => res.json())
      .then(setData);
  }, [url]);

  return <pre>{JSON.stringify(data)}</pre>;
}
