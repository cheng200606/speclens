import { Suspense, use } from "react";

function Status() {
  const data = use(fetch("/api/status").then((res) => res.json()));
  return <p>{String(data.ok)}</p>;
}

export function Page() {
  return (
    <Suspense fallback="loading">
      <Status />
    </Suspense>
  );
}
