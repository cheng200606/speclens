import { use, Suspense } from "react";

type User = { name: string };

function Profile({ userPromise }: { userPromise: Promise<User> }) {
  // Promise 直接交给 use，pending 与错误都由 React/Suspense 处理，
  // 不读取 promise.status / promise.value
  const user = use(userPromise);
  return <p>{user.name}</p>;
}

export function ProfilePage({ userPromise }: { userPromise: Promise<User> }) {
  return (
    <Suspense fallback="loading profile">
      <Profile userPromise={userPromise} />
    </Suspense>
  );
}
