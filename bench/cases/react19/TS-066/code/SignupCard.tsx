import { useActionState } from "react";

async function join(_prev: boolean, formData: FormData): Promise<boolean> {
  await fetch("/api/signup", { method: "POST", body: formData });
  return true;
}

export function SignupCard() {
  const [done, formAction, isPending] = useActionState(join, false);

  return (
    <form action={formAction}>
      <input name="email" disabled={isPending} />
      <button type="submit" disabled={isPending}>Join</button>
      {done && <p>joined</p>}
    </form>
  );
}
