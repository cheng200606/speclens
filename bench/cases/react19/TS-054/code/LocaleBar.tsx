import { use, Suspense } from "react";

declare function browserLocales(): Promise<string[]>;

function LocaleTag() {
  const locales = use(browserLocales());
  return <span>{locales[0]}</span>;
}

export function LocaleBar() {
  return (
    <Suspense fallback="...">
      <LocaleTag />
    </Suspense>
  );
}
