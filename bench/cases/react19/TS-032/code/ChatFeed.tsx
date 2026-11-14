import { useOptimistic, startTransition } from "react";

const history: string[] = [];

export function ChatFeed({ messages }: { messages: string[] }) {
  const [feed, addMessage] = useOptimistic(messages, (current, next: string) => {
    // 不纯：修改模块级外部数组 + 依赖当前时间
    history.push(next);
    return [...current, `[${Date.now()}] ${next}`];
  });

  function handleSend(text: string) {
    startTransition(async () => {
      addMessage(text);
      await fetch("/api/messages", { method: "POST", body: text });
    });
  }

  return (
    <div>
      <button onClick={() => handleSend("hello")}>Send hello</button>
      {feed.map((m, i) => (
        <p key={i}>{m}</p>
      ))}
    </div>
  );
}
