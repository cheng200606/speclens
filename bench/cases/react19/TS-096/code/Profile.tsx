import { use } from "react";

type Profile = { handle: string };
const cache = new Map<string, Promise<Profile>>();

function getProfile(id: string): Promise<Profile> {
  if (!cache.has(id)) cache.set(id, fetch(`/api/profile/${id}`).then((r) => r.json()));
  return cache.get(id)!;
}

export function Profile({ id }: { id: string }) {
  const profile = use(getProfile(id));
  return <p>@{profile.handle}</p>;
}
