import { useEffect, useState } from "react";

type User = { id: string; name: string };

export function Profile({ userId }: { userId: string }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    let ignore = false;
    fetch(`/api/users/${userId}`)
      .then((res) => res.json())
      .then((data: User) => {
        if (!ignore) setUser(data);
      });
    return () => {
      ignore = true;
    };
  }, [userId]);

  return <div>{user?.name ?? "loading"}</div>;
}
