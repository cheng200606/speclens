// good: arrow function callback (variant 2)
queue.subscribe((event) => {
  dispatch(event.type, event.payload);
});
