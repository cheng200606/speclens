// good: object destructuring (variant 2)
export function findItems(order) {
  const { symbol, quote, amount } = order;
  return { pair: `${symbol}/${quote}`, amount };
}
