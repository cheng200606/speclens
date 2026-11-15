import { useActionState } from "react";

async function vote(_prev: string, formData: FormData): Promise<string> {
  const choice = String(formData.get("choice") ?? "");
  await fetch("/api/vote", { method: "POST", body: choice });
  return choice;
}

export function VoteForm() {
  const [choice, formAction, isPending] = useActionState(vote, "");

  return (
    <form action={formAction}>
      <input name="choice" disabled={isPending} />
      <button type="submit" disabled={isPending}>Vote</button>
      <p>{choice}</p>
    </form>
  );
}
