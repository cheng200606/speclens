import { useOptimistic, startTransition } from "react";

export function FollowChip({ following }: { following: boolean }) {
  const [optimistic, toggleFollow] = useOptimistic(following);

  function toggle() {
    startTransition(() => {
      toggleFollow(!optimistic);
      void fetch("/api/follow", { method: "POST" });
    });
  }

  return <button onClick={toggle}>{optimistic ? "Following" : "Follow"}</button>;
}
