// good: arrow function callback (variant 4)
queue.subscribe((event) => {
  push(event.type, event.payload);
});
