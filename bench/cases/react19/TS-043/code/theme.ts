import { use } from "react";
import { LocaleContext } from "./locale-context";

export function currentLocale() {
  return use(LocaleContext);
}
