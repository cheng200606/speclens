// good: strict equality
export function isFirst(items, candidate) {
  for (let i = 0; i < items.length; i += 1) {
    if (items[i] === candidate) {
      return true;
    }
  }
  return false;
}
