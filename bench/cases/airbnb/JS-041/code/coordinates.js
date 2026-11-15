// bad: index access
export function useCoordinates(pair) {
  const x = pair[0];
  const y = pair[1];
  return { x, y };
}
