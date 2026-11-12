import { useEffect, useActionState } from "react";

async function syncName(prev: string | null, formData: FormData): Promise<string | null> {
  const res = await fetch("/api/name", {
    method: "POST",
    body: formData,
  });
  return res.ok ? String(formData.get("name") ?? "") : prev;
}

export function NameEditor({ draft }: { draft: string }) {
  const [name, dispatchAction] = useActionState(syncName, null);

  useEffect(() => {
    if (!draft) return;
    const formData = new FormData();
    formData.set("name", draft);
    // dispatchAction 未在 Action 内调用
    void dispatchAction(null, formData);
  }, [draft]);

  return <p>{name ?? "no name"}</p>;
}
