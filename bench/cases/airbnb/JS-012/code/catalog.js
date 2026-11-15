// bad: repeated property access (variant 2)
export function findItems(order) {
  const pair = `${order.symbol}/${order.quote}`;
  const amount = order.amount;
  return { pair, amount };
}
