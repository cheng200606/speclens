import { useActionState, startTransition } from "react";

async function addMember(prev: string | null, email: string): Promise<string | null> {
  const res = await fetch("/api/members", { method: "POST", body: email });
  return res.ok ? email : prev;
}

export function Inviter() {
  const [member, dispatchAction, isPending] = useActionState(addMember, null);

  function invite() {
    startTransition(() => {
      dispatchAction("new-member@example.com");
    });
  }

  return (
    <button onClick={invite} disabled={isPending}>Invite</button>
  );
}
