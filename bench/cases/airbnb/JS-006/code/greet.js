// good: default parameter syntax
export function greet(options) {
  const { greeting = "Hello", name } = options;
  return `${greeting}, ${name}!`;
}
