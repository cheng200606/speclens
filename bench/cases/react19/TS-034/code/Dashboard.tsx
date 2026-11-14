import { useEffect, useState } from "react";

export function Dashboard({ url }: { url: string }) {
  const [data, setData] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    // 手动管理 loading/error 的 Effect 取数（R-001：应使用 use() + 缓存），
    // 且无清理/中止逻辑：url 变化后旧响应可能晚到覆盖新数据（R-003）
    setLoading(true);
    fetch(url)
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((e) => {
        setError(e as Error);
        setLoading(false);
      });
  }, [url]);

  if (loading) return <p>loading...</p>;
  if (error) return <p>error</p>;
  return <pre>{JSON.stringify(data)}</pre>;
}
