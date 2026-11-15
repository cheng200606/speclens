// bad: function expression callback (variant 3)
queue.subscribe(function (event) {
  record(event.type, event.payload);
});
