import { useState } from "react";

export function VoteForm() {
  const [choice, setChoice] = useState("");

  function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    void fetch("/api/vote", { method: "POST", body: choice });
  }

  return (
    <form onSubmit={submit}>
      <input value={choice} onChange={(e) => setChoice(e.target.value)} />
      <button type="submit">Vote</button>
    </form>
  );
}
