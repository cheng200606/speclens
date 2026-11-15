// bad: var declaration
var apiKey = "sk-test";
var retries = 3;

function withRetry(fn) {
  var attempt = 0;
  return function () {
    attempt += 1;
    return attempt <= retries ? fn() : null;
  };
}

module.exports = { withRetry };
