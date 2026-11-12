import { useState, useTransition } from "react";

export function TodoList({ todos }: { todos: string[] }) {
  const [isPending, startTransition] = useTransition();
  const [doneIds, setDoneIds] = useState<string[]>([]);

  function markDone(id: string) {
    setDoneIds((prev) => [...prev, id]);
    startTransition(async () => {
      await fetch(`/api/todos/${id}/done`, { method: "POST" });
    });
  }

  return (
    <ul>
      {todos.map((id) => (
        <li
          key={id}
          style={{ opacity: doneIds.includes(id) && !isPending ? 1 : 0.5 }}
        >
          {id}
          <button onClick={() => markDone(id)}>done</button>
        </li>
      ))}
    </ul>
  );
}
