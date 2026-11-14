import { useState } from "react";

export function SignupForm() {
  const [name, setName] = useState("");
  const [status, setStatus] = useState<"idle" | "saving" | "done">("idle");

  // 手动 onSubmit + setState 处理表单提交，未使用 Actions（useActionState / action 属性）
  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus("saving");
    await fetch("/api/signup", { method: "POST", body: JSON.stringify({ name }) });
    setStatus("done");
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={name} onChange={(e) => setName(e.target.value)} />
      <button type="submit">{status === "saving" ? "Saving..." : "Sign up"}</button>
      {status === "done" && <p>signed up</p>}
    </form>
  );
}
