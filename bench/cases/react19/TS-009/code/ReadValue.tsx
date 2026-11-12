import { Suspense } from "react";
import { fetchData } from "./api";

type Resource = { status: "pending" | "fulfilled"; value?: string };

export function ReadValue({ url }: { url: string }) {
  const promise = fetchData(url) as Promise<string> & Resource;
  // 绕过 use，直接读 promise.value
  const text = promise.status === "fulfilled" ? promise.value ?? "" : "";
  return <Suspense fallback="loading"><p>{text}</p></Suspense>;
}
