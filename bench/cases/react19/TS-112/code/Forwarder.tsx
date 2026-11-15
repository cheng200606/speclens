import { useActionState, startTransition, useEffect } from "react";

async function forward(prev: string | null, payload: string): Promise<string | null> {
  const res = await fetch("/api/forward", { method: "POST", body: payload });
  return res.ok ? payload : prev;
}

export function Forwarder() {
  const [sent, dispatchAction, isPending] = useActionState(forward, null);

  useEffect(() => {
    const id = setInterval(() => {
      startTransition(() => {
        dispatchAction("queued");
      });
    }, 10000);
    return () => clearInterval(id);
  }, []);

  return <p>{sent ?? "idle"} {isPending ? "(pending)" : ""}</p>;
}
