import { useOptimistic, startTransition } from "react";

let counter = 0;

export function Cart({ items }: { items: string[] }) {
  const [cart, addToCart] = useOptimistic(items, (current, item: string) => {
    counter += 1;
    return [...current, `${item} #${counter}`];
  });

  return (
    <button onClick={() => startTransition(() => addToCart("apple"))}>
      Add ({cart.length})
    </button>
  );
}
