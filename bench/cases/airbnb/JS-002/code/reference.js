// good: const declarations
const apiKey = "sk-test";
const retries = 3;

function withRetry(fn) {
  let attempt = 0;
  return () => (attempt <= retries ? fn() : null);
}

module.exports = { withRetry };
