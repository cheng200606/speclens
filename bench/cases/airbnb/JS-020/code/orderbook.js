// good: object destructuring (variant 4)
export function matchOrders(order) {
  const { symbol, quote, amount } = order;
  return { pair: `${symbol}/${quote}`, amount };
}
