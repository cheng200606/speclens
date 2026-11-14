import { useEffect, useState } from "react";

export function Heartbeat({ onPing }: { onPing: () => void }) {
  const [beat, setBeat] = useState(0);

  useEffect(() => {
    // 建立 定时器 + 事件订阅，均返回清理函数
    const id = setInterval(() => {
      setBeat((b) => b + 1);
      onPing();
    }, 1000);
    window.addEventListener("online", onPing);
    return () => {
      clearInterval(id);
      window.removeEventListener("online", onPing);
    };
  }, [onPing]);

  return <p>beats: {beat}</p>;
}
