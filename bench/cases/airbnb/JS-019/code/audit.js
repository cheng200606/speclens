// good: object destructuring (variant 3)
export function logItems(order) {
  const { symbol, quote, amount } = order;
  return { pair: `${symbol}/${quote}`, amount };
}
