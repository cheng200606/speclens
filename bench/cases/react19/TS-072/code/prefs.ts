import { use } from "react";
import { PrefsContext } from "./prefs-context";

export function usePrefs() {
  return use(PrefsContext);
}
