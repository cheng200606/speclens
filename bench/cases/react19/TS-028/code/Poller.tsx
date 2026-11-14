import { useEffect, useState } from "react";

export function Poller({ endpoint }: { endpoint: string }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    // 建立定时器但未返回清理函数：
    // endpoint 变化时旧 interval 泄漏并继续轮询旧地址
    const id = setInterval(() => {
      fetch(endpoint).then(() => setCount((c) => c + 1));
    }, 2000);
    console.log("polling", endpoint, id);
  }, [endpoint]);

  return <p>polled {count} times</p>;
}
