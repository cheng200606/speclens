// bad: function expression callback (variant 2)
queue.subscribe(function (event) {
  dispatch(event.type, event.payload);
});
