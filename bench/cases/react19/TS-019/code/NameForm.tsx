import { useActionState } from "react";

type FormState = { error: string | null };

async function submitAction(_prev: FormState, formData: FormData): Promise<FormState> {
  const name = String(formData.get("name") ?? "");
  if (name.trim().length < 2) {
    return { error: "name too short" };
  }
  await fetch("/api/name", { method: "POST", body: formData });
  return { error: null };
}

export function NameForm() {
  const [state, submitFormAction, isPending] = useActionState(submitAction, { error: null });
  // 提交交给 form 的 action prop：React 自动包 Transition 并传 FormData
  return (
    <form action={submitFormAction}>
      <input name="name" disabled={isPending} />
      <button type="submit" disabled={isPending}>Save</button>
      {state.error && <p role="alert">{state.error}</p>}
    </form>
  );
}
