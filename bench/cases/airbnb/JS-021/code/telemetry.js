// bad: function expression callback (variant 1)
queue.subscribe(function (event) {
  emit(event.type, event.payload);
});
