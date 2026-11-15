import { useOptimistic } from "react";

export function FollowChip({ following }: { following: boolean }) {
  const [optimistic, toggleFollow] = useOptimistic(following);

  toggleFollow(!following);

  return <span>{optimistic ? "Following" : "Follow"}</span>;
}
