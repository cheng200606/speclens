import { use } from "react";

type Data = { url: string };

export function Avatar({ dataPromise }: { dataPromise: Promise<Data> & { value?: Data } }) {
  const url = dataPromise.value?.url ?? "default.png";
  return <img src={url} alt="avatar" />;
}
