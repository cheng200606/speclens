import { useOptimistic, startTransition } from "react";

export function LikeButton({
  isLiked,
  onToggle,
}: {
  isLiked: boolean;
  onToggle: (v: boolean) => Promise<void>;
}) {
  const [optimisticLiked, setOptimisticLiked] = useOptimistic(isLiked);

  function handleClick() {
    startTransition(async () => {
      // setter 在 Action（startTransition 包裹的异步函数）内调用
      setOptimisticLiked(!optimisticLiked);
      await onToggle(!optimisticLiked);
    });
  }

  return <button onClick={handleClick}>{optimisticLiked ? "Liked" : "Like"}</button>;
}
