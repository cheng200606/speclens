import { useState } from "react";

export function Newsletter() {
  const [done, setDone] = useState(false);

  function subscribe(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    void fetch("/api/subscribe", { method: "POST", body: new FormData(e.currentTarget) });
    setDone(true);
  }

  return (
    <form onSubmit={subscribe}>
      <input name="email" />
      <button type="submit">Subscribe</button>
      {done && <p>subscribed</p>}
    </form>
  );
}
