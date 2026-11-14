import { use } from "react";
import { fetchUser } from "./api";

type User = { name: string };

export function UserCard({ userId }: { userId: string }) {
  // fetchUser 是未缓存的 async 函数：每次渲染都会创建新 Promise，
  // 即使写法上像普通数据请求，也会让 Suspense 在每次重渲染时反复回退
  const user = use(fetchUser(userId));
  return <p>{user.name}</p>;
}
