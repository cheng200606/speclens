import { useActionState } from "react";

async function pushNote(prev: string | null, note: string): Promise<string | null> {
  const res = await fetch("/api/notes", { method: "POST", body: note });
  return res.ok ? note : prev;
}

export function NotePusher() {
  const [note, dispatchAction, isPending] = useActionState(pushNote, null);

  function handlePush() {
    setTimeout(() => {
      dispatchAction("deferred note");
    }, 800);
  }

  return (
    <div>
      <button onClick={handlePush} disabled={isPending}>Push later</button>
      {note && <p>pushed: {note}</p>}
    </div>
  );
}
