import { useOptimistic, startTransition } from "react";

export function Cart({ items }: { items: string[] }) {
  const [cart, addToCart] = useOptimistic(items, (current, item: string) => [
    ...current,
    item,
  ]);

  return (
    <button onClick={() => startTransition(() => addToCart("apple"))}>
      Add ({cart.length})
    </button>
  );
}
