// good: object destructuring (variant 1)
export function listItems(order) {
  const { symbol, quote, amount } = order;
  return { pair: `${symbol}/${quote}`, amount };
}
