import { useState, useTransition } from "react";

export function FollowCount({ initial }: { initial: number }) {
  const [count, setCount] = useState(initial);
  const [pending, startTransition] = useTransition();

  function handleFollow() {
    // 手动提前 +1 模拟“乐观更新”，未使用 useOptimistic；
    // 失败回滚全靠手写，与规范推荐的 useOptimistic 模式相悖
    setCount((c) => c + 1);
    startTransition(async () => {
      try {
        await fetch("/api/follow", { method: "POST" });
      } catch {
        setCount((c) => c - 1);
      }
    });
  }

  return (
    <button onClick={handleFollow} disabled={pending}>
      {count} followers
    </button>
  );
}
