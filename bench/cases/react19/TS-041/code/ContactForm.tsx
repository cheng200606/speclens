import { useState } from "react";

export function ContactForm() {
  const [sent, setSent] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    await fetch("/api/contact", { method: "POST", body: form });
    setSent(true);
  }

  return (
    <form onSubmit={handleSubmit}>
      <input name="message" />
      <button type="submit">Send</button>
      {sent && <p>sent</p>}
    </form>
  );
}
