// bad: mutating function arguments for defaults
export function greet(options) {
  if (options.greeting === undefined) {
    options.greeting = "Hello";
  }
  return `${options.greeting}, ${options.name}!`;
}
