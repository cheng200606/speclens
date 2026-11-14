import { useOptimistic } from "react";

export function CartCount({ count }: { count: number }) {
  const [optimisticCount, setOptimisticCount] = useOptimistic(count);

  function handleAdd() {
    // setter 直接在普通事件回调里调用，未包 startTransition/Action，
    // 乐观状态会一闪而过并立即回退
    setOptimisticCount((c) => c + 1);
    void fetch("/api/cart", { method: "POST" });
  }

  return <button onClick={handleAdd}>{optimisticCount} in cart</button>;
}
