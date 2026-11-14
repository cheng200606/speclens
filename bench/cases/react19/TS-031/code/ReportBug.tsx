import { useActionState } from "react";

async function sendReport(prev: string | null, payload: string): Promise<string | null> {
  const res = await fetch("/api/report", { method: "POST", body: payload });
  return res.ok ? payload : prev;
}

export function ReportBug() {
  const [state, dispatchAction, isPending] = useActionState(sendReport, null);

  function handleClick() {
    // dispatchAction 延迟到 setTimeout 回调中执行，
    // 已脱离任何 Action / Transition 作用域
    setTimeout(() => {
      dispatchAction("user-report");
    }, 0);
  }

  return (
    <div>
      <button onClick={handleClick} disabled={isPending}>Send report</button>
      {state && <p>reported: {state}</p>}
    </div>
  );
}
