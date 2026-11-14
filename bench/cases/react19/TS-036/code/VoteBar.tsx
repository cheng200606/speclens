import { useOptimistic, startTransition } from "react";

export function VoteBar({
  votes,
  onVote,
}: {
  votes: number;
  onVote: () => Promise<void>;
}) {
  const [optimisticVotes, setOptimisticVotes] = useOptimistic(votes);

  function handleVote() {
    startTransition(async () => {
      await onVote();
      // setter 在 await 之后调用：此时 Transition 可能已随 await 结束，
      // 乐观状态可能来不及呈现；稳妥写法是先 set 再 await，
      // 或在 await 之后用二次 startTransition 包裹
      setOptimisticVotes((v) => v + 1);
    });
  }

  return <button onClick={handleVote}>{optimisticVotes} votes</button>;
}
