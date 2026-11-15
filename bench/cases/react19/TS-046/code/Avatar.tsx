import { use } from "react";

type Data = { url: string };

export function Avatar({ dataPromise }: { dataPromise: Promise<Data> }) {
  const data = use(dataPromise);
  return <img src={data.url} alt="avatar" />;
}
