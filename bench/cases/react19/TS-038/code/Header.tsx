import { use, Suspense } from "react";

declare function browserTime(): Promise<string>;

function CurrentTime() {
  // 服务端渲染期间读取 browser-only 值
  const time = use(browserTime());
  return <span>{time}</span>;
}

export function Header() {
  return (
    <header>
      {/* Suspense 只包住侧栏：CurrentTime 不在任何 Suspense 边界内，
          服务端渲染会直接失败 */}
      <Suspense fallback="...">
        <aside>menu</aside>
      </Suspense>
      <CurrentTime />
    </header>
  );
}
