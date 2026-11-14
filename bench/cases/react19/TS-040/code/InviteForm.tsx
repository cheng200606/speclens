import { useState, useActionState } from "react";

async function invite(prev: string | null, email: string): Promise<string | null> {
  const res = await fetch("/api/invite", { method: "POST", body: email });
  return res.ok ? email : prev;
}

export function InviteForm() {
  const [email, setEmail] = useState("");
  const [invited, dispatchAction] = useActionState(invite, null);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    // 双重问题：手动 onSubmit 处理表单提交（未用 Actions），
    // 且 dispatchAction 在普通事件回调中直接调用（不在 Action 内）
    dispatchAction(email);
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={email} onChange={(e) => setEmail(e.target.value)} />
      <button type="submit">Invite</button>
      {invited && <p>invited {invited}</p>}
    </form>
  );
}
