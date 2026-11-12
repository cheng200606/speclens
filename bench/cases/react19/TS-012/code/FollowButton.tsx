import { useOptimistic, useState } from "react";

export function FollowButton() {
  const [following, setFollowing] = useState(false);
  const [optimisticFollowing, setOptimisticFollowing] = useOptimistic(following);

  function handleClick() {
    // setter 在普通事件回调中调用，未包进 Action/startTransition
    setOptimisticFollowing(true);
    void fetch("/api/follow", { method: "POST" }).then(() => setFollowing(true));
  }

  return (
    <button onClick={handleClick}>
      {optimisticFollowing ? "Following" : "Follow"}
    </button>
  );
}
