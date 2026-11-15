import { use } from "react";

type Profile = { handle: string };

export function Profile({ id }: { id: string }) {
  const profile = use(profileFetch(id));
  return <p>@{profile.handle}</p>;
}

async function profileFetch(id: string): Promise<Profile> {
  const res = await fetch(`/api/profile/${id}`);
  return res.json();
}
