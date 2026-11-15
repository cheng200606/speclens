import { use } from "react";
import { UserContext } from "./user-context";

export function onProfileOpen() {
  const user = use(UserContext);
  openProfile(user.id);
}
