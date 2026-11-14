import { useOptimistic, startTransition } from "react";

type Todo = { id: number; text: string };
type Action = { type: "add"; todo: Todo } | { type: "remove"; id: number };

function todosReducer(current: Todo[], action: Action): Todo[] {
  // 纯函数：只依据入参计算新状态，不改外部变量、不依赖时间
  switch (action.type) {
    case "add":
      return [...current, action.todo];
    case "remove":
      return current.filter((t) => t.id !== action.id);
  }
}

export function TodoList({ todos }: { todos: Todo[] }) {
  const [optimisticTodos, dispatch] = useOptimistic(todos, todosReducer);

  function handleAdd(todo: Todo) {
    startTransition(async () => {
      dispatch({ type: "add", todo });
      await fetch("/api/todos", { method: "POST", body: JSON.stringify(todo) });
    });
  }

  return (
    <div>
      <button onClick={() => handleAdd({ id: Date.now(), text: "new todo" })}>Add</button>
      <ul>
        {optimisticTodos.map((t) => (
          <li key={t.id}>{t.text}</li>
        ))}
      </ul>
    </div>
  );
}
