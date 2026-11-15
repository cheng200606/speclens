// bad: repeated property access (variant 4)
export function matchOrders(order) {
  const pair = `${order.symbol}/${order.quote}`;
  const amount = order.amount;
  return { pair, amount };
}
