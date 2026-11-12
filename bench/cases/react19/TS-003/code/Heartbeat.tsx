import { useEffect } from "react";

export function Heartbeat() {
  useEffect(() => {
    setInterval(() => {
      console.log("beat");
    }, 1000);
  }, []);

  return <p>alive</p>;
}
