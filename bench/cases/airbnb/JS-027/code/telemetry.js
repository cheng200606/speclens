// good: arrow function callback (variant 1)
queue.subscribe((event) => {
  emit(event.type, event.payload);
});
