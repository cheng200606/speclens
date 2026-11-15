"""I5 第二批 synthetic 案例（agents-sdk PY-009..016、asvs PY-117..124、react19 TS-051..060）。

一次性生成脚本（用后保留作为复现依据）。确定性输出。
"""

from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def w(root: pathlib.Path, cid: str, verdict: str, rid: str, fname: str, diff: str, note: str, code: str) -> None:
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


# ---- agents-sdk 第二批（PY-009..016，4v/4c）----
AG = ROOT / "bench" / "cases" / "agents-sdk"

w(AG, "PY-009", "violation", "agents-007", "router.py", "hard",
  "两个目的地只注册了一个 handoff()，第二个目的地靠指令文字提示模型直接调用，违反 agents-007（每目的地一 handoff）。",
  '''from agents import Agent, handoff

billing = Agent(name="Billing", instructions="Handle billing questions.")
refunds = Agent(name="Refunds", instructions="Handle refund requests.")

triage = Agent(
    name="Triage",
    instructions="Route billing or refunds questions to the right agent.",
    handoffs=[handoff(billing)],
)
''')
w(AG, "PY-010", "compliant", "agents-007", "router.py", "hard",
  "每个目的地各注册一个 handoff()，模型在两者间选择，符合 agents-007。",
  '''from agents import Agent, handoff

billing = Agent(name="Billing", instructions="Handle billing questions.")
refunds = Agent(name="Refunds", instructions="Handle refund requests.")

triage = Agent(
    name="Triage",
    instructions="Route billing or refunds questions to the right agent.",
    handoffs=[handoff(billing), handoff(refunds)],
)
''')
w(AG, "PY-011", "violation", "agents-008", "rewrite.py", "medium",
  "自定义 model input 回调返回 dict 而非 ModelInputData，违反 agents-008。",
  '''from agents import Agent

def prepare_input(agent, input_items) -> dict:
    return {"input": input_items}
''')
w(AG, "PY-012", "compliant", "agents-008", "rewrite.py", "medium",
  "回调返回 ModelInputData 且 input 为输入项列表，符合 agents-008。",
  '''from agents import Agent
from agents.run import ModelInputData

def prepare_input(agent, input_items) -> ModelInputData:
    return ModelInputData(input=input_items)
''')
w(AG, "PY-013", "violation", "agents-004", "gatekeeper.py", "medium",
  "意图是省昂贵模型开销却用并行 guardrail（tripwire 触发前模型已启动），违反 agents-004。",
  '''from agents import Agent, InputGuardrail

gatekeeper = Agent(name="Gatekeeper", instructions="Block policy-violating input.")

guardrail = InputGuardrail(guardrail_agent=gatekeeper, run_in_parallel=True)

assistant = Agent(
    name="Assistant",
    instructions="Expensive assistant model.",
    input_guardrails=[guardrail],
)
''')
w(AG, "PY-014", "compliant", "agents-004", "gatekeeper.py", "medium",
  "阻塞式 guardrail（run_in_parallel=False），tripwire 触发时昂贵模型不启动，符合 agents-004。",
  '''from agents import Agent, InputGuardrail

gatekeeper = Agent(name="Gatekeeper", instructions="Block policy-violating input.")

guardrail = InputGuardrail(guardrail_agent=gatekeeper, run_in_parallel=False)

assistant = Agent(
    name="Assistant",
    instructions="Expensive assistant model.",
    input_guardrails=[guardrail],
)
''')
w(AG, "PY-015", "violation", "agents-003", "moderator.py", "medium",
  "对不可信用户输入的筛查放在昂贵模型完成之后，未用 input_guardrails 在输入侧并行校验，违反 agents-003。",
  '''from agents import Agent

assistant = Agent(name="Assistant", instructions="Answer user questions.")

async def moderate_then_answer(user_input: str) -> str:
    result = await Runner.run(assistant, user_input)
    await screen_for_policy_violations(user_input)
    return result.final_output
''')
w(AG, "PY-016", "compliant", "agents-003", "moderator.py", "medium",
  "用 input_guardrails 在 agent 运行的同时对用户输入做校验，符合 agents-003。",
  '''from agents import Agent, InputGuardrail

screen = Agent(name="Screen", instructions="Screen input for policy violations.")

guardrail = InputGuardrail(guardrail_agent=screen)

assistant = Agent(
    name="Assistant",
    instructions="Answer user questions.",
    input_guardrails=[guardrail],
)
''')

# ---- asvs 第二批（PY-117..124，4v/4c）----
AS = ROOT / "bench" / "cases" / "asvs"

w(AS, "PY-117", "violation", "asvs-V6.2.10", "password_policy.py", "medium",
  "强制 90 天轮换密码，违反 asvs-V6.2.10（不得要求周期性轮换）。",
  '''from datetime import datetime, timedelta

def needs_rotation(user) -> bool:
    return datetime.now() - user.password_changed_at > timedelta(days=90)
''')
w(AS, "PY-118", "compliant", "asvs-V6.2.10", "password_policy.py", "medium",
  "密码有效直至发现泄露或用户主动更换，无强制轮换，符合 asvs-V6.2.10。",
  '''def needs_rotation(user) -> bool:
    return user.password_compromised
''')
w(AS, "PY-119", "violation", "asvs-V6.4.3", "reset.py", "hard",
  "忘记密码重置直接建立新会话，绕过已启用的 MFA，违反 asvs-V6.4.3。",
  '''@app.post("/reset-password")
def reset_password(token: str = Form(...), password: str = Form(...)):
    if validate_reset_token(token):
        user = user_from_token(token)
        set_password(user, password)
        start_session(user)
        return {"ok": True}
    raise HTTPException(status_code=400)
''')
w(AS, "PY-120", "compliant", "asvs-V6.4.3", "reset.py", "hard",
  "重置流程要求先通过 MFA 再建立会话，符合 asvs-V6.4.3。",
  '''@app.post("/reset-password")
def reset_password(token: str = Form(...), password: str = Form(...), otp: str = Form(...)):
    if validate_reset_token(token) and verify_mfa(user_from_token(token), otp):
        user = user_from_token(token)
        set_password(user, password)
        start_session(user)
        return {"ok": True}
    raise HTTPException(status_code=400)
''')
w(AS, "PY-121", "violation", "asvs-V6.5.4", "otp.py", "medium",
  "OTP 为 4 位纯数字（约 13.3 bits），低于 20 bits 熵要求，违反 asvs-V6.5.4。",
  '''import secrets

def generate_otp() -> str:
    return f"{secrets.randbelow(10000):04d}"
''')
w(AS, "PY-122", "compliant", "asvs-V6.5.4", "otp.py", "medium",
  "OTP 为 6 位 base32 字母数字（约 28 bits），符合 asvs-V6.5.4。",
  '''import secrets

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"

def generate_otp() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(6))
''')
w(AS, "PY-123", "violation", "asvs-V7.5.2", "sessions.py", "medium",
  "用户无法查看/终止自己的活动会话（无任何用户侧会话管理端点），违反 asvs-V7.5.2。",
  '''@app.get("/me")
def me(user=Depends(current_user)):
    return {"name": user.name}
''')
w(AS, "PY-124", "compliant", "asvs-V7.5.2", "sessions.py", "medium",
  "提供查看并二次认证后终止自己全部会话的端点，符合 asvs-V7.5.2。",
  '''@app.get("/me/sessions")
def list_sessions(user=Depends(current_user)):
    return db.active_sessions(user)

@app.post("/me/sessions/revoke")
def revoke_sessions(password: str = Form(...), user=Depends(current_user)):
    if not verify_password(user, password):
        raise HTTPException(status_code=403)
    db.revoke_sessions(user)
    return {"ok": True}
''')

# ---- react19 第二批（TS-051..060，5v/5c）----
RR = ROOT / "bench" / "cases" / "react19"

w(RR, "TS-051", "violation", "R-005", "SubmitButton.tsx", "medium",
  "提交前手动 setState 预置成功文案模拟乐观反馈，未用 useOptimistic。",
  '''import { useState } from "react";

export function SubmitButton() {
  const [label, setLabel] = useState("Save");

  async function handleSave() {
    setLabel("Saved!");
    await fetch("/api/save", { method: "POST" });
  }

  return <button onClick={handleSave}>{label}</button>;
}
''')
w(RR, "TS-052", "compliant", "R-005", "SubmitButton.tsx", "medium",
  "乐观反馈用 useOptimistic 实现并在 Action 中调用 setter。",
  '''import { useOptimistic, startTransition } from "react";

export function SubmitButton() {
  const [label, setLabel] = useOptimistic("Save");

  async function handleSave() {
    startTransition(async () => {
      setLabel("Saved!");
      await fetch("/api/save", { method: "POST" });
    });
  }

  return <button onClick={handleSave}>{label}</button>;
}
''')
w(RR, "TS-053", "violation", "R-008", "LocaleBar.tsx", "hard",
  "服务端渲染读取 browser 值的组件不在任何 Suspense 边界内。",
  '''import { use } from "react";

declare function browserLocales(): Promise<string[]>;

export function LocaleBar() {
  const locales = use(browserLocales());
  return <span>{locales[0]}</span>;
}
''')
w(RR, "TS-054", "compliant", "R-008", "LocaleBar.tsx", "hard",
  "调用 use(browserLocales()) 的组件被 Suspense 边界包裹，SSR 可用。",
  '''import { use, Suspense } from "react";

declare function browserLocales(): Promise<string[]>;

function LocaleTag() {
  const locales = use(browserLocales());
  return <span>{locales[0]}</span>;
}

export function LocaleBar() {
  return (
    <Suspense fallback="...">
      <LocaleTag />
    </Suspense>
  );
}
''')
w(RR, "TS-055", "compliant", "R-001", "Activity.tsx", "medium",
  "取数走 use() 与缓存 fetcher，无 Effect 手动取数。",
  '''import { use, Suspense } from "react";

const cache = new Map<string, Promise<unknown>>();

function getActivity(url: string): Promise<unknown> {
  if (!cache.has(url)) {
    cache.set(url, fetch(url).then((res) => res.json()));
  }
  return cache.get(url)!;
}

function Feed({ url }: { url: string }) {
  const data = use(getActivity(url));
  return <pre>{JSON.stringify(data)}</pre>;
}

export function Activity({ url }: { url: string }) {
  return (
    <Suspense fallback="loading">
      <Feed url={url} />
    </Suspense>
  );
}
''')
w(RR, "TS-056", "violation", "R-001", "Activity.tsx", "medium",
  "useEffect + setState 手动取数（无缓存、无清理），未用 use()。",
  '''import { useEffect, useState } from "react";

export function Activity({ url }: { url: string }) {
  const [data, setData] = useState<unknown>(null);

  useEffect(() => {
    fetch(url)
      .then((res) => res.json())
      .then(setData);
  }, [url]);

  return <pre>{JSON.stringify(data)}</pre>;
}
''')
w(RR, "TS-057", "violation", "R-006", "profile.ts", "easy",
  "use() 在普通回调函数中调用，非组件/Hook。",
  '''import { use } from "react";
import { UserContext } from "./user-context";

export function onProfileOpen() {
  const user = use(UserContext);
  openProfile(user.id);
}
''')
w(RR, "TS-058", "compliant", "R-006", "profile.ts", "easy",
  "use() 在自定义 Hook 内调用，符合 R-006。",
  '''import { use } from "react";
import { UserContext } from "./user-context";

export function useUser() {
  return use(UserContext);
}
''')
w(RR, "TS-059", "compliant", "R-007", "Query.tsx", "hard",
  "按参数键控的缓存 Promise 交给 use，重渲染复用同一实例。",
  '''import { use } from "react";

type Row = { id: number };
const cache = new Map<string, Promise<Row[]>>();

function getRows(query: string): Promise<Row[]> {
  if (!cache.has(query)) {
    cache.set(query, fetch(`/api/rows?q=${query}`).then((r) => r.json()));
  }
  return cache.get(query)!;
}

export function Query({ query }: { query: string }) {
  const rows = use(getRows(query));
  return <ul>{rows.map((row) => <li key={row.id}>{row.id}</li>)}</ul>;
}
''')
w(RR, "TS-060", "compliant", "R-003", "Ticker.tsx", "medium",
  "Effect 建立事件订阅并返回清理函数。",
  '''import { useEffect, useState } from "react";

export function Ticker({ source }: { source: EventTarget }) {
  const [ticks, setTicks] = useState(0);

  useEffect(() => {
    const onTick = () => setTicks((t) => t + 1);
    source.addEventListener("tick", onTick);
    return () => source.removeEventListener("tick", onTick);
  }, [source]);

  return <p>ticks: {ticks}</p>;
}
''')

print("batch2: agents-sdk +8, asvs +8, react19 +10 = 26 cases")
