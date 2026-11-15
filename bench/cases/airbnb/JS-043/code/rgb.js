// bad: index access (variant)
export function toRGB triplet(hex) {
  const parts = hexToParts(hex);
  return { r: parts[0], g: parts[1], b: parts[2] };
}
