import { use } from "react";
import { PrefsContext } from "./prefs-context";

export function readPrefs() {
  return use(PrefsContext);
}
