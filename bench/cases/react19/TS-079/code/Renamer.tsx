import { useActionState } from "react";

async function rename(prev: string | null, name: string): Promise<string | null> {
  const res = await fetch("/api/rename", { method: "POST", body: name });
  return res.ok ? name : prev;
}

export function Renamer() {
  const [renamed, dispatchAction, isPending] = useActionState(rename, null);

  function commit() {
    void Promise.resolve().then(() => dispatchAction("new-name"));
  }

  return (
    <div>
      <button onClick={commit} disabled={isPending}>Rename</button>
      {renamed && <p>renamed: {renamed}</p>}
    </div>
  );
}
