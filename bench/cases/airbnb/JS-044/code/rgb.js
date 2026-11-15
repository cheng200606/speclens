// good: array destructuring (variant)
export function toRGBTriplet(hex) {
  const [r, g, b] = hexToParts(hex);
  return { r, g, b };
}
