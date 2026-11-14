import { useActionState, startTransition } from "react";

async function saveDraft(_prev: string | null, payload: string): Promise<string | null> {
  const res = await fetch("/api/draft", { method: "POST", body: payload });
  return res.ok ? payload : _prev;
}

export function DraftBox() {
  const [saved, dispatchAction, isPending] = useActionState(saveDraft, null);

  function handleSave() {
    // dispatchAction 包在 startTransition（Action）内调用
    startTransition(() => {
      dispatchAction("auto-save");
    });
  }

  return (
    <div>
      <button onClick={handleSave} disabled={isPending}>Save</button>
      {saved && <p>saved: {saved}</p>}
    </div>
  );
}
