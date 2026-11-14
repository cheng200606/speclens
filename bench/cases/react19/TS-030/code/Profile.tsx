import { use } from "react";

type User = { name: string };
type Statusful<T> = Promise<T> & { status?: "pending" | "fulfilled" | "rejected" };

export function Profile({ userPromise }: { userPromise: Statusful<User> }) {
  // 先读 promise.status 手工分流，绕过 use 的 Suspense 语义；
  // use 也因此位于条件分支内
  if (userPromise.status === "pending") {
    return <p>loading...</p>;
  }
  const user = use(userPromise);
  return <p>{user.name}</p>;
}
