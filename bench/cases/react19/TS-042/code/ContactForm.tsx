import { useActionState } from "react";

async function send(_prev: boolean, formData: FormData): Promise<boolean> {
  await fetch("/api/contact", { method: "POST", body: formData });
  return true;
}

export function ContactForm() {
  const [sent, formAction, isPending] = useActionState(send, false);

  return (
    <form action={formAction}>
      <input name="message" disabled={isPending} />
      <button type="submit" disabled={isPending}>Send</button>
      {sent && <p>sent</p>}
    </form>
  );
}
