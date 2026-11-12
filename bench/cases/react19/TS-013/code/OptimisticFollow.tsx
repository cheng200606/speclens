import { useOptimistic, useState, useTransition } from "react";

export function OptimisticFollow() {
  const [following, setFollowing] = useState(false);
  const [isPending, startTransition] = useTransition();
  const [optimisticFollowing, addOptimistic] = useOptimistic(
    following,
    (current, delta: boolean) => delta
  );

  function handleClick() {
    startTransition(async () => {
      addOptimistic(true);
      await fetch("/api/follow", { method: "POST" });
      setFollowing(true);
    });
  }

  return (
    <button onClick={handleClick} disabled={isPending}>
      {optimisticFollowing ? "Following" : "Follow"}
    </button>
  );
}
