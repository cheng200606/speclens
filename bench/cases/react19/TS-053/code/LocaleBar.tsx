import { use } from "react";

declare function browserLocales(): Promise<string[]>;

export function LocaleBar() {
  const locales = use(browserLocales());
  return <span>{locales[0]}</span>;
}
