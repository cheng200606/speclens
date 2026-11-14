import { use } from "react";

type User = { name: string };

// 模块级“缓存”：单槽位，且不按参数区分
let cached: { key: string; promise: Promise<User> } | null = null;

function getUser(userId: string): Promise<User> {
  if (!cached || cached.key !== userId) {
    cached = {
      key: userId,
      promise: fetch("/api/user/" + userId).then((r) => r.json()),
    };
  }
  return cached.promise;
}

export function UserBadge({ userId }: { userId: string }) {
  // 同一 userId 的重渲染复用同一 Promise 实例（满足 R-007 字面要求），
  // 但不同 userId 的组件实例交替渲染会互相踢掉缓存，
  // 使对方的每次渲染都新建 Promise——缓存粒度与使用方式存在隐含耦合
  const user = use(getUser(userId));
  return <p>{user.name}</p>;
}
