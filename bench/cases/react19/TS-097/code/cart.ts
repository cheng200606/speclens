import { use } from "react";
import { CartContext } from "./cart-context";

export function cartTotal() {
  const cart = use(CartContext);
  return cart.items.reduce((sum, i) => sum + i.price, 0);
}
