// bad: repeated property access (variant 1)
export function listItems(order) {
  const pair = `${order.symbol}/${order.quote}`;
  const amount = order.amount;
  return { pair, amount };
}
