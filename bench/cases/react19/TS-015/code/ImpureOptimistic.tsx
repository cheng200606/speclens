import { useOptimistic, useTransition } from "react";

const log: string[] = [];

export function ImpureOptimistic() {
  const [isPending, startTransition] = useTransition();
  const [optimistic, addOptimistic] = useOptimistic(false, (current) => {
    // 非纯：修改外部状态 + 依赖当前时间
    log.push(`update at ${Date.now()}`);
    return !current;
  });

  function handleClick() {
    startTransition(async () => {
      addOptimistic(true);
      await fetch("/api/toggle", { method: "POST" });
    });
  }

  return (
    <button onClick={handleClick} disabled={isPending}>
      {String(optimistic)}
    </button>
  );
}
