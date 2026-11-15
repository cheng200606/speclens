// good: arrow function callback (variant 3)
queue.subscribe((event) => {
  record(event.type, event.payload);
});
