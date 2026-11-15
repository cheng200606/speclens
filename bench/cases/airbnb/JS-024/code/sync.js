// bad: function expression callback (variant 4)
queue.subscribe(function (event) {
  push(event.type, event.payload);
});
