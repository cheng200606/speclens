import { useState } from "react";

export function SignupCard() {
  const [done, setDone] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    await fetch("/api/signup", { method: "POST", body: new FormData(e.currentTarget) });
    setDone(true);
  }

  return (
    <form onSubmit={onSubmit}>
      <input name="email" />
      <button type="submit">Join</button>
      {done && <p>joined</p>}
    </form>
  );
}
