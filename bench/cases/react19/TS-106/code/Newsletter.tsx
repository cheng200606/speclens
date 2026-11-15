import { useActionState } from "react";

async function subscribe(_prev: boolean, formData: FormData): Promise<boolean> {
  await fetch("/api/subscribe", { method: "POST", body: formData });
  return true;
}

export function Newsletter() {
  const [done, formAction, isPending] = useActionState(subscribe, false);

  return (
    <form action={formAction}>
      <input name="email" disabled={isPending} />
      <button type="submit" disabled={isPending}>Subscribe</button>
      {done && <p>subscribed</p>}
    </form>
  );
}
