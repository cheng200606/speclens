// good: array destructuring
export function useCoordinates(pair) {
  const [x, y] = pair;
  return { x, y };
}
