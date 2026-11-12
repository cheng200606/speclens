import { useActionState } from "react";

async function updateName(
  _prev: string | null,
  formData: FormData,
): Promise<string | null> {
  const name = String(formData.get("name") ?? "");
  const res = await fetch("/api/name", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  if (!res.ok) return null;
  return name;
}

export function NameForm() {
  const [name, formAction, isPending] = useActionState(updateName, null);

  return (
    <form action={formAction}>
      <input name="name" defaultValue={name ?? ""} />
      <button type="submit" disabled={isPending}>
        Update
      </button>
    </form>
  );
}
