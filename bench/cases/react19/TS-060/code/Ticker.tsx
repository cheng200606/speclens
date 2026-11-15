import { useEffect, useState } from "react";

export function Ticker({ source }: { source: EventTarget }) {
  const [ticks, setTicks] = useState(0);

  useEffect(() => {
    const onTick = () => setTicks((t) => t + 1);
    source.addEventListener("tick", onTick);
    return () => source.removeEventListener("tick", onTick);
  }, [source]);

  return <p>ticks: {ticks}</p>;
}
