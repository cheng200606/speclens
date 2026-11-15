// bad: repeated property access (variant 3)
export function logItems(order) {
  const pair = `${order.symbol}/${order.quote}`;
  const amount = order.amount;
  return { pair, amount };
}
