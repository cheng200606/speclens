"""I5 第四批 +20 案例（凑 240）：react19 8、airbnb 4、agents-sdk 4、asvs 4。"""

from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def w(root, cid, verdict, rid, fname, diff, note, code):
    d = root / cid / "code"
    d.mkdir(parents=True, exist_ok=True)
    (d / fname).write_text(code, encoding="utf-8", newline="\n")
    meta = f'''case_id: {cid}
verdict: {verdict}
difficulty: {diff}
rule_ids: [{rid}]
origin: synthetic
files: ["code/{fname}"]
annotations:
  - annotator: A
    verdict: {verdict}
    rule_ids: [{rid}]
    notes: "{note}（AI 起草，待人工复核后可升 handcrafted。）"
resolved:
  verdict: {verdict}
  rule_ids: [{rid}]
'''
    (root / cid / "meta.yaml").write_text(meta, encoding="utf-8", newline="\n")


def main():
    n = 0
    rr = ROOT / "bench" / "cases" / "react19"

    # react19 8（R-002/R-005/R-007/R-011 各一对新语境变体）
    pairs = [
        ("TS-105", "violation", "R-002", "Newsletter.tsx", "medium", "手动订阅表单（新语境）。",
         '''import { useState } from "react";

export function Newsletter() {
  const [done, setDone] = useState(false);

  function subscribe(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    void fetch("/api/subscribe", { method: "POST", body: new FormData(e.currentTarget) });
    setDone(true);
  }

  return (
    <form onSubmit={subscribe}>
      <input name="email" />
      <button type="submit">Subscribe</button>
      {done && <p>subscribed</p>}
    </form>
  );
}
'''),
        ("TS-106", "compliant", "R-002", "Newsletter.tsx", "medium", "action prop 订阅表单（新语境）。",
         '''import { useActionState } from "react";

async function subscribe(_prev: boolean, formData: FormData): Promise<boolean> {
  await fetch("/api/subscribe", { method: "POST", body: formData });
  return true;
}

export function Newsletter() {
  const [done, formAction, isPending] = useActionState(subscribe, false);

  return (
    <form action={formAction}>
      <input name="email" disabled={isPending} />
      <button type="submit" disabled={isPending}>Subscribe</button>
      {done && <p>subscribed</p>}
    </form>
  );
}
'''),
        ("TS-107", "violation", "R-005", "DeleteCard.tsx", "medium", "手动乐观删除（新语境）。",
         '''import { useState } from "react";

export function DeleteCard({ title }: { title: string }) {
  const [deleted, setDeleted] = useState(false);

  function remove() {
    setDeleted(true);
    void fetch("/api/cards", { method: "DELETE" });
  }

  return deleted ? null : <button onClick={remove}>Delete {title}</button>;
}
'''),
        ("TS-108", "compliant", "R-005", "DeleteCard.tsx", "medium", "useOptimistic 删除（新语境）。",
         '''import { useOptimistic } from "react";

export function DeleteCard({ title }: { title: string }) {
  const [deleted, remove] = useOptimistic(false);

  function removeCard() {
    startTransition(() => {
      remove(true);
      void fetch("/api/cards", { method: "DELETE" });
    });
  }

  if (deleted) return null;
  return <button onClick={removeCard}>Delete {title}</button>;
}

import { startTransition } from "react";
'''),
        ("TS-109", "violation", "R-007", "Stats.tsx", "medium", "use(fetch(...)) 内联（新语境）。",
         '''import { use } from "react";

export function Stats({ slug }: { slug: string }) {
  const stats = use(fetch(`/api/stats/${slug}`).then((r) => r.json()));
  return <p>{stats.views} views</p>;
}
'''),
        ("TS-110", "compliant", "R-007", "Stats.tsx", "medium", "缓存 + use()（新语境）。",
         '''import { use } from "react";

const cache = new Map<string, Promise<{ views: number }>>();

function getStats(slug: string): Promise<{ views: number }> {
  if (!cache.has(slug)) cache.set(slug, fetch(`/api/stats/${slug}`).then((r) => r.json()));
  return cache.get(slug)!;
}

export function Stats({ slug }: { slug: string }) {
  const stats = use(getStats(slug));
  return <p>{stats.views} views</p>;
}
'''),
        ("TS-111", "violation", "R-011", "Forwarder.tsx", "medium", "dispatch 在 interval 回调（新语境）。",
         '''import { useActionState, useEffect } from "react";

async function forward(prev: string | null, payload: string): Promise<string | null> {
  const res = await fetch("/api/forward", { method: "POST", body: payload });
  return res.ok ? payload : prev;
}

export function Forwarder() {
  const [sent, dispatchAction, isPending] = useActionState(forward, null);

  useEffect(() => {
    const id = setInterval(() => {
      dispatchAction("queued");
    }, 10000);
    return () => clearInterval(id);
  }, []);

  return <p>{sent ?? "idle"} {isPending ? "(pending)" : ""}</p>;
}
'''),
        ("TS-112", "compliant", "R-011", "Forwarder.tsx", "medium", "dispatch 在 Action + interval 正确清理（新语境）。",
         '''import { useActionState, startTransition, useEffect } from "react";

async function forward(prev: string | null, payload: string): Promise<string | null> {
  const res = await fetch("/api/forward", { method: "POST", body: payload });
  return res.ok ? payload : prev;
}

export function Forwarder() {
  const [sent, dispatchAction, isPending] = useActionState(forward, null);

  useEffect(() => {
    const id = setInterval(() => {
      startTransition(() => {
        dispatchAction("queued");
      });
    }, 10000);
    return () => clearInterval(id);
  }, []);

  return <p>{sent ?? "idle"} {isPending ? "(pending)" : ""}</p>;
}
'''),
    ]
    for cid, verdict, rule, fname, diff, note, code in pairs:
        w(rr, cid, verdict, rule, fname, diff, note, code)
        n += 1

    # airbnb 4（airbnb-003 数组解构 两对）
    ab = ROOT / "bench" / "cases" / "airbnb"
    w(ab, "JS-041", "violation", "airbnb-003", "coordinates.js", "easy",
      "多返回值用下标访问而非数组解构，违反 airbnb-003。",
      '''// bad: index access
export function useCoordinates(pair) {
  const x = pair[0];
  const y = pair[1];
  return { x, y };
}
''')
    w(ab, "JS-042", "compliant", "airbnb-003", "coordinates.js", "easy",
      "数组解构，符合 airbnb-003。",
      '''// good: array destructuring
export function useCoordinates(pair) {
  const [x, y] = pair;
  return { x, y };
}
''')
    w(ab, "JS-043", "violation", "airbnb-003", "rgb.js", "easy",
      "下标访问返回数组（变体），违反 airbnb-003。",
      '''// bad: index access (variant)
export function toRGB triplet(hex) {
  const parts = hexToParts(hex);
  return { r: parts[0], g: parts[1], b: parts[2] };
}
''')
    w(ab, "JS-044", "compliant", "airbnb-003", "rgb.js", "easy",
      "数组解构（变体），符合 airbnb-003。",
      '''// good: array destructuring (variant)
export function toRGBTriplet(hex) {
  const [r, g, b] = hexToParts(hex);
  return { r, g, b };
}
''')
    n += 4

    # agents-sdk 4（agents-007/008 各一对新语境）
    ag = ROOT / "bench" / "cases" / "agents-sdk"
    w(ag, "PY-029", "violation", "agents-007", "escalation.py", "medium",
      "三个目的地只注册一个 handoff（新语境），违反 agents-007。",
      '''from agents import Agent, handoff

general = Agent(name="General", instructions="General support.")
billing = Agent(name="Billing", instructions="Billing.")
technical = Agent(name="Technical", instructions="Technical issues.")

support = Agent(
    name="Support",
    handoffs=[handoff(general)],
)
''')
    w(ag, "PY-030", "compliant", "agents-007", "escalation.py", "medium",
      "每个目的地各一 handoff（新语境），符合 agents-007。",
      '''from agents import Agent, handoff

general = Agent(name="General", instructions="General support.")
billing = Agent(name="Billing", instructions="Billing.")
technical = Agent(name="Technical", instructions="Technical issues.")

support = Agent(
    name="Support",
    handoffs=[handoff(general), handoff(billing), handoff(technical)],
)
''')
    w(ag, "PY-031", "violation", "agents-008", "custom_input.py", "medium",
      "回调返回 list 而非 ModelInputData（新语境），违反 agents-008。",
      '''from agents import RunConfig

def make_input(agent, items):
    return items
''')
    w(ag, "PY-032", "compliant", "agents-008", "custom_input.py", "medium",
      "回调返回 ModelInputData（新语境），符合 agents-008。",
      '''from agents import RunConfig
from agents.run import ModelInputData

def make_input(agent, items):
    return ModelInputData(input=items)
''')
    n += 4

    # asvs 4（V6.4.3 / V6.5.1 各一对新语境）
    asv = ROOT / "bench" / "cases" / "asvs"
    w(asv, "PY-137", "violation", "asvs-V6.4.3", "forgot.py", "medium",
      "重置后直接登录态返回（新语境），违反 asvs-V6.4.3。",
      '''@app.post("/forgot/confirm")
def forgot_confirm(email: str = Form(...), code: str = Form(...), new: str = Form(...)):
    if check_email_code(email, code):
        set_password(email, new)
        login(email)
        return {"ok": True}
    raise HTTPException(status_code=400)
''')
    w(asv, "PY-138", "compliant", "asvs-V6.4.3", "forgot.py", "medium",
      "重置后要求重新完整认证（含 MFA），符合 asvs-V6.4.3。",
      '''@app.post("/forgot/confirm")
def forgot_confirm(email: str = Form(...), code: str = Form(...), new: str = Form(...), mfa: str = Form(...)):
    if check_email_code(email, code) and verify_mfa(email, mfa):
        set_password(email, new)
        return {"ok": True, "next": "login"}
    raise HTTPException(status_code=400)
''')
    w(asv, "PY-139", "violation", "asvs-V6.5.1", "login_otp.py", "medium",
      "登录 OTP 校验通过未消费（新语境），违反 asvs-V6.5.1。",
      '''@app.post("/login/otp")
def login_otp(user: str = Form(...), code: str = Form(...)):
    if get_otp(user) == code:
        return {"token": issue_token(user)}
    raise HTTPException(status_code=401)
''')
    w(asv, "PY-140", "compliant", "asvs-V6.5.1", "login_otp.py", "medium",
      "登录 OTP 一次性消费（新语境），符合 asvs-V6.5.1。",
      '''@app.post("/login/otp")
def login_otp(user: str = Form(...), code: str = Form(...)):
    if consume_otp(user, code):
        return {"token": issue_token(user)}
    raise HTTPException(status_code=401)
''')
    n += 4

    print(f"batch4: {n} cases")


if __name__ == "__main__":
    main()
