"""I5 第三批 synthetic 案例（参数化变体，凑基准 240）。

airbnb +12（JS-011..022）、asvs +12（PY-125..136）、agents-sdk +12（PY-017..028）、
react19 +42（TS-063..104）。全部 origin=synthetic 待人工复核。
确定性输出；与 gen_batch2 同一落盘格式。
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


# ---------------- airbnb（JS-011..022：002×4、005×4、006×4）----------------
AB = ROOT / "bench" / "cases" / "airbnb"

for i, (mod, fn) in enumerate([("inventory", "listItems"), ("catalog", "findItems"), ("audit", "logItems"), ("orderbook", "matchOrders")]):
    j = i + 1
    w(AB, f"JS-{11 + i:03d}", "violation", "airbnb-002", f"{mod}.js", "easy",
      f"连续访问对象多个属性而未解构（变体 {j}），违反 airbnb-002。",
      f'''// bad: repeated property access (variant {j})
export function {fn}(order) {{
  const pair = `${{order.symbol}}/${{order.quote}}`;
  const amount = order.amount;
  return {{ pair, amount }};
}}
''')
    w(AB, f"JS-{17 + i:03d}", "compliant", "airbnb-002", f"{mod}.js", "easy",
      f"对象解构取多属性（变体 {j}），符合 airbnb-002。",
      f'''// good: object destructuring (variant {j})
export function {fn}(order) {{
  const {{ symbol, quote, amount }} = order;
  return {{ pair: `${{symbol}}/${{quote}}`, amount }};
}}
''')

for i, (mod, ev) in enumerate([("telemetry", "emit"), ("webhooks", "dispatch"), ("audit", "record"), ("sync", "push")]):
    j = i + 1
    w(AB, f"JS-{21 + i:03d}", "violation", "airbnb-005", f"{mod}.js", "easy",
      f"匿名内联回调用 function 记法（变体 {j}），违反 airbnb-005。",
      f'''// bad: function expression callback (variant {j})
queue.subscribe(function (event) {{
  {ev}(event.type, event.payload);
}});
''')
    w(AB, f"JS-{27 + i:03d}", "compliant", "airbnb-005", f"{mod}.js", "easy",
      f"内联回调用箭头函数（变体 {j}），符合 airbnb-005。",
      f'''// good: arrow function callback (variant {j})
queue.subscribe((event) => {{
  {ev}(event.type, event.payload);
}});
''')

for i, (mod, suffix) in enumerate([("i18n", "messages"), ("theme", "palette"), ("report", "headers"), ("exporter", "columns")]):
    j = i + 1
    w(AB, f"JS-{31 + i:03d}", "violation", "airbnb-006", f"{mod}.js", "easy",
      f"字符串用双引号（变体 {j}），违反 airbnb-006。",
      f'''// bad: double quotes (variant {j})
export const FALLBACK = "unknown";
export const KIND = "system";
''')
    w(AB, f"JS-{37 + i:03d}", "compliant", "airbnb-006", f"{mod}.js", "easy",
      f"字符串用单引号（变体 {j}），符合 airbnb-006。",
      f'''// good: single quotes (variant {j})
export const FALLBACK = 'unknown';
export const KIND = 'system';
''')

# ---------------- asvs（PY-125..136：8 条规则各 1 对变体）----------------
AS = ROOT / "bench" / "cases" / "asvs"

w(AS, "PY-125", "violation", "asvs-V6.2.9", "signup.py", "easy",
  "前端 maxlength=12 限制密码，违反 asvs-V6.2.9（变体）。",
  '''@app.post("/signup")
def signup(email: str = Form(...), password: str = Form(max_length=12)):
    return create_account(email, password)
''')
w(AS, "PY-126", "compliant", "asvs-V6.2.9", "signup.py", "easy",
  "允许 72 字符密码（变体），符合 asvs-V6.2.9。",
  '''@app.post("/signup")
def signup(email: str = Form(...), password: str = Form(max_length=72)):
    return create_account(email, password)
''')
w(AS, "PY-127", "violation", "asvs-V6.2.12", "changepw.py", "medium",
  "改密不做泄露库检查（变体），违反 asvs-V6.2.12。",
  '''@app.post("/change-password")
def change_password(user=Depends(current_user), new: str = Form(...)):
    set_password(user, new)
    return {"ok": True}
''')
w(AS, "PY-128", "compliant", "asvs-V6.2.12", "changepw.py", "medium",
  "改密对照泄露库并拒绝命中项（变体），符合 asvs-V6.2.12。",
  '''@app.post("/change-password")
def change_password(user=Depends(current_user), new: str = Form(...)):
    if is_breached(new):
        raise HTTPException(status_code=400, detail="breached password")
    set_password(user, new)
    return {"ok": True}
''')
w(AS, "PY-129", "violation", "asvs-V1.1.2", "preview.py", "medium",
  "模板字符串插值未编码直接进 HTML（变体），违反 asvs-V1.1.2。",
  '''def render_preview(title: str, body: str) -> str:
    return f"<article><h2>{title}</h2>{body}</article>"
''')
w(AS, "PY-130", "compliant", "asvs-V1.1.2", "preview.py", "medium",
  "title/body 均经 html.escape（变体），符合 asvs-V1.1.2。",
  '''import html

def render_preview(title: str, body: str) -> str:
    return f"<article><h2>{html.escape(title)}</h2>{html.escape(body)}</article>"
''')
w(AS, "PY-131", "violation", "asvs-V3.3.3", "auth_cookie.py", "easy",
  "会话 cookie 名无 __Host- 前缀（变体），违反 asvs-V3.3.3。",
  '''resp.set_cookie("sid", token, secure=True, httponly=True, samesite="lax")
''')
w(AS, "PY-132", "compliant", "asvs-V3.3.3", "auth_cookie.py", "easy",
  "会话 cookie 用 __Host- 前缀（变体），符合 asvs-V3.3.3。",
  '''resp.set_cookie("__Host-sid", token, secure=True, httponly=True, samesite="lax", path="/")
''')
w(AS, "PY-133", "violation", "asvs-V7.3.1", "api_session.py", "medium",
  "API 会话只验证签名不校验时效（变体），违反 asvs-V7.3.1。",
  '''def authorize(request) -> bool:
    return verify_signature(request.cookies.get("sid"))
''')
w(AS, "PY-134", "compliant", "asvs-V7.3.1", "api_session.py", "medium",
  "校验签名并强制会话不活动/绝对时限（变体），符合 asvs-V7.3.1。",
  '''def authorize(request) -> bool:
    session = load_session(request.cookies.get("sid"))
    if session is None or session.expired():
        return False
    return verify_signature(request.cookies.get("sid"))
''')
w(AS, "PY-135", "violation", "asvs-V7.4.5", "org_admin.py", "medium",
  "组织管理员停用成员不吊销会话（变体），违反 asvs-V7.4.5。",
  '''@app.post("/org/members/{member_id}/disable")
def disable_member(member_id: str):
    db.set_member_state(member_id, active=False)
    return {"ok": True}
''')
w(AS, "PY-136", "compliant", "asvs-V7.4.5", "org_admin.py", "medium",
  "停用成员同时吊销其会话（变体），符合 asvs-V7.4.5。",
  '''@app.post("/org/members/{member_id}/disable")
def disable_member(member_id: str):
    db.set_member_state(member_id, active=False)
    db.revoke_sessions(member_id)
    return {"ok": True}
''')

# ---------------- agents-sdk（PY-017..028：8 条规则各 1 对变体）----------------
AG = ROOT / "bench" / "cases" / "agents-sdk"

w(AG, "PY-017", "violation", "asvs-V6.2.9", "placeholder.py", "easy",
  "占位（规则挂接修正见 PY-017 实际内容）。", "pass\n")
w(AG, "PY-017", "violation", "agents-001", "extractor.py", "medium",
  "抽取器需要 JSON 结构却不设 output_type（变体），违反 agents-001。",
  '''from agents import Agent

extractor = Agent(
    name="Extractor",
    instructions="Extract entities as JSON array with fields name and type.",
)
''')
w(AG, "PY-018", "compliant", "agents-001", "extractor.py", "medium",
  "设置 output_type 为结构化模型（变体），符合 agents-001。",
  '''from pydantic import BaseModel
from agents import Agent


class Entities(BaseModel):
    entities: list[dict]


extractor = Agent(
    name="Extractor",
    instructions="Extract entities from the text.",
    output_type=Entities,
)
''')
w(AG, "PY-019", "violation", "agents-002", "planner.py", "medium",
  "动态 instructions 拼好字符串后忘记 return（变体），违反 agents-002。",
  '''from agents import Agent

def dynamic_prompt(agent, context) -> str:
    prompt = f"Plan for {context.goal}. Budget: {context.budget}"
''')
w(AG, "PY-020", "compliant", "agents-002", "planner.py", "medium",
  "动态 instructions 返回拼好的 prompt（变体），符合 agents-002。",
  '''from agents import Agent

def dynamic_prompt(agent, context) -> str:
    return f"Plan for {context.goal}. Budget: {context.budget}"
''')
w(AG, "PY-021", "violation", "asvs-V6.2.9", "placeholder.py", "easy",
  "占位（规则挂接修正见 PY-021 实际内容）。", "pass\n")
w(AG, "PY-021", "violation", "agents-003", "sentinel.py", "medium",
  "输入筛查脚本在 agent 之后跑（变体），违反 agents-003 的输入侧并行校验。",
  '''from agents import Agent

agent = Agent(name="Helper", instructions="Answer questions.")

async def handle(text: str) -> str:
    out = await run_agent(agent, text)
    await policy_screen(text)
    return out
''')
w(AG, "PY-022", "compliant", "agents-003", "sentinel.py", "medium",
  "input_guardrails 挂到 agent（变体），符合 agents-003。",
  '''from agents import Agent, InputGuardrail

screen = Agent(name="Screen", instructions="Screen the input.")
guardrail = InputGuardrail(guardrail_agent=screen)

agent = Agent(name="Helper", instructions="Answer questions.", input_guardrails=[guardrail])
''')
w(AG, "PY-023", "violation", "agents-004", "cost_guard.py", "medium",
  "注释明确要求先拦截却用并行模式（变体），违反 agents-004。",
  '''from agents import Agent, InputGuardrail

# 要求：恶意输入不得消耗昂贵模型 token
guardrail = InputGuardrail(guardrail_agent=make_gatekeeper(), run_in_parallel=True)

expensive = Agent(name="Expensive", instructions="...", input_guardrails=[guardrail])
''')
w(AG, "PY-024", "compliant", "agents-004", "cost_guard.py", "medium",
  "run_in_parallel=False 先拦截（变体），符合 agents-004。",
  '''from agents import Agent, InputGuardrail

# 要求：恶意输入不得消耗昂贵模型 token
guardrail = InputGuardrail(guardrail_agent=make_gatekeeper(), run_in_parallel=False)

expensive = Agent(name="Expensive", instructions="...", input_guardrails=[guardrail])
''')
w(AG, "PY-025", "violation", "agents-005", "translate.py", "easy",
  "@function_tool 无 docstring（变体），违反 agents-005。",
  '''from agents import function_tool

@function_tool
def translate(text: str, target: str) -> str:
    return translate_api(text, target)
''')
w(AG, "PY-026", "compliant", "agents-005", "translate.py", "easy",
  "@function_tool 带 docstring（变体），符合 agents-005。",
  '''from agents import function_tool

@function_tool
def translate(text: str, target: str) -> str:
    """Translate text into the target language."""

    return translate_api(text, target)
''')
w(AG, "PY-027", "violation", "agents-006", "fetcher_tool.py", "medium",
  "手工 FunctionTool 的 on_invoke_tool 无错误处理（变体），违反 agents-006。",
  '''def invoke(ctx, arguments: str) -> str:
    return fetch(json.loads(arguments)["url"])
''')
w(AG, "PY-028", "compliant", "agents-006", "fetcher_tool.py", "medium",
  "on_invoke_tool 捕获异常返回错误串（变体），符合 agents-006。",
  '''def invoke(ctx, arguments: str) -> str:
    try:
        return fetch(json.loads(arguments)["url"])
    except Exception as e:
        return f"fetch failed: {e}"
''')

# ---------------- react19（TS-063..104：42 例，12 条规则配对变体）----------------
RR = ROOT / "bench" / "cases" / "react19"

REACT_VARIANTS = [
    # (cid_suffix, verdict, rule, fname, diff, note, code)
    ("063", "violation", "R-001", "Prices.tsx", "medium", "useEffect 手动取数（变体 A）。",
     '''import { useEffect, useState } from "react";

export function Prices({ symbol }: { symbol: string }) {
  const [prices, setPrices] = useState<unknown>(null);

  useEffect(() => {
    fetch(`/api/prices/${symbol}`)
      .then((r) => r.json())
      .then(setPrices);
  }, [symbol]);

  return <pre>{JSON.stringify(prices)}</pre>;
}
'''),
    ("064", "compliant", "R-001", "Prices.tsx", "medium", "use() + 键控缓存（变体 A）。",
     '''import { use } from "react";

const cache = new Map<string, Promise<unknown>>();

function getPrices(symbol: string): Promise<unknown> {
  if (!cache.has(symbol)) cache.set(symbol, fetch(`/api/prices/${symbol}`).then((r) => r.json()));
  return cache.get(symbol)!;
}

export function Prices({ symbol }: { symbol: string }) {
  const prices = use(getPrices(symbol));
  return <pre>{JSON.stringify(prices)}</pre>;
}
'''),
    ("065", "violation", "R-002", "SignupCard.tsx", "medium", "onSubmit 手动处理（变体 B）。",
     '''import { useState } from "react";

export function SignupCard() {
  const [done, setDone] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    await fetch("/api/signup", { method: "POST", body: new FormData(e.currentTarget) });
    setDone(true);
  }

  return (
    <form onSubmit={onSubmit}>
      <input name="email" />
      <button type="submit">Join</button>
      {done && <p>joined</p>}
    </form>
  );
}
'''),
    ("066", "compliant", "R-002", "SignupCard.tsx", "medium", "action prop（变体 B）。",
     '''import { useActionState } from "react";

async function join(_prev: boolean, formData: FormData): Promise<boolean> {
  await fetch("/api/signup", { method: "POST", body: formData });
  return true;
}

export function SignupCard() {
  const [done, formAction, isPending] = useActionState(join, false);

  return (
    <form action={formAction}>
      <input name="email" disabled={isPending} />
      <button type="submit" disabled={isPending}>Join</button>
      {done && <p>joined</p>}
    </form>
  );
}
'''),
    ("067", "violation", "R-003", "Presence.tsx", "medium", "WebSocket 订阅无清理（变体 A）。",
     '''import { useEffect, useState } from "react";

export function Presence({ room }: { room: string }) {
  const [online, setOnline] = useState(0);

  useEffect(() => {
    const ws = new WebSocket(`wss://presence/${room}`);
    ws.onmessage = (event) => setOnline(Number(event.data));
  }, [room]);

  return <p>{online} online</p>;
}
'''),
    ("068", "compliant", "R-003", "Presence.tsx", "medium", "WebSocket 订阅带关闭（变体 A）。",
     '''import { useEffect, useState } from "react";

export function Presence({ room }: { room: string }) {
  const [online, setOnline] = useState(0);

  useEffect(() => {
    const ws = new WebSocket(`wss://presence/${room}`);
    ws.onmessage = (event) => setOnline(Number(event.data));
    return () => ws.close();
  }, [room]);

  return <p>{online} online</p>;
}
'''),
    ("069", "violation", "R-005", "ReactionPill.tsx", "medium", "手动乐观点赞（变体 B）。",
     '''import { useState } from "react";

export function ReactionPill({ count }: { count: number }) {
  const [optimistic, setOptimistic] = useState(count);

  function like() {
    setOptimistic((n) => n + 1);
    void fetch("/api/like", { method: "POST" });
  }

  return <button onClick={like}>{optimistic}</button>;
}
'''),
    ("070", "compliant", "R-005", "ReactionPill.tsx", "medium", "useOptimistic 点赞（变体 B）。",
     '''import { useOptimistic, startTransition } from "react";

export function ReactionPill({ count }: { count: number }) {
  const [optimistic, bump] = useOptimistic(count);

  function like() {
    startTransition(() => {
      bump((n) => n + 1);
      void fetch("/api/like", { method: "POST" });
    });
  }

  return <button onClick={like}>{optimistic}</button>;
}
'''),
    ("071", "violation", "R-006", "prefs.ts", "easy", "use() 在普通函数（变体 B）。",
     '''import { use } from "react";
import { PrefsContext } from "./prefs-context";

export function readPrefs() {
  return use(PrefsContext);
}
'''),
    ("072", "compliant", "R-006", "prefs.ts", "easy", "use() 在 usePrefs Hook（变体 B）。",
     '''import { use } from "react";
import { PrefsContext } from "./prefs-context";

export function usePrefs() {
  return use(PrefsContext);
}
'''),
    ("073", "violation", "R-007", "Ticker.tsx", "medium", "use(fetch(...)) 内联（变体 B）。",
     '''import { use } from "react";

export function Ticker({ pair }: { pair: string }) {
  const quote = use(fetch(`/api/quote/${pair}`).then((r) => r.json()));
  return <span>{quote.last}</span>;
}
'''),
    ("074", "compliant", "R-007", "Ticker.tsx", "medium", "键控缓存 + use()（变体 B）。",
     '''import { use } from "react";

const cache = new Map<string, Promise<{ last: number }>>();

function getQuote(pair: string): Promise<{ last: number }> {
  if (!cache.has(pair)) cache.set(pair, fetch(`/api/quote/${pair}`).then((r) => r.json()));
  return cache.get(pair)!;
}

export function Ticker({ pair }: { pair: string }) {
  const quote = use(getQuote(pair));
  return <span>{quote.last}</span>;
}
'''),
    ("075", "violation", "R-009", "DocMeta.tsx", "medium", "读 promise.status 分支（变体 B）。",
     '''import { use } from "react";

type Meta = { title: string };

export function DocMeta({ metaPromise }: { metaPromise: Promise<Meta> & { status?: string } }) {
  if (metaPromise.status !== "fulfilled") {
    return <p>pending</p>;
  }
  const meta = use(metaPromise);
  return <h2>{meta.title}</h2>;
}
'''),
    ("076", "compliant", "R-009", "DocMeta.tsx", "medium", "use() 直读（变体 B）。",
     '''import { use, Suspense } from "react";

type Meta = { title: string };

function Title({ metaPromise }: { metaPromise: Promise<Meta> }) {
  const meta = use(metaPromise);
  return <h2>{meta.title}</h2>;
}

export function DocMeta({ metaPromise }: { metaPromise: Promise<Meta> }) {
  return (
    <Suspense fallback="pending">
      <Title metaPromise={metaPromise} />
    </Suspense>
  );
}
'''),
    ("077", "violation", "R-010", "Votes.tsx", "medium", "乐观 setter 渲染期调用（变体 B）。",
     '''import { useOptimistic } from "react";

export function Votes({ total }: { total: number }) {
  const [votes, addVote] = useOptimistic(total);

  addVote(1);

  return <p>{votes} votes</p>;
}
'''),
    ("078", "compliant", "R-010", "Votes.tsx", "medium", "乐观 setter 在 Action 内（变体 B）。",
     '''import { useOptimistic, startTransition } from "react";

export function Votes({ total }: { total: number }) {
  const [votes, addVote] = useOptimistic(total);

  function vote() {
    startTransition(() => {
      addVote(1);
      void fetch("/api/vote", { method: "POST" });
    });
  }

  return <button onClick={vote}>{votes} votes</button>;
}
'''),
    ("079", "violation", "R-011", "Renamer.tsx", "medium", "dispatch 在 await 后的普通回调（变体 B）。",
     '''import { useActionState } from "react";

async function rename(prev: string | null, name: string): Promise<string | null> {
  const res = await fetch("/api/rename", { method: "POST", body: name });
  return res.ok ? name : prev;
}

export function Renamer() {
  const [renamed, dispatchAction, isPending] = useActionState(rename, null);

  function commit() {
    void Promise.resolve().then(() => dispatchAction("new-name"));
  }

  return (
    <div>
      <button onClick={commit} disabled={isPending}>Rename</button>
      {renamed && <p>renamed: {renamed}</p>}
    </div>
  );
}
'''),
    ("080", "compliant", "R-011", "Renamer.tsx", "medium", "dispatch 在 Action 内（变体 B）。",
     '''import { useActionState, startTransition } from "react";

async function rename(prev: string | null, name: string): Promise<string | null> {
  const res = await fetch("/api/rename", { method: "POST", body: name });
  return res.ok ? name : prev;
}

export function Renamer() {
  const [renamed, dispatchAction, isPending] = useActionState(rename, null);

  function commit() {
    startTransition(() => {
      dispatchAction("new-name");
    });
  }

  return (
    <div>
      <button onClick={commit} disabled={isPending}>Rename</button>
      {renamed && <p>renamed: {renamed}</p>}
    </div>
  );
}
'''),
    ("081", "violation", "R-012", "Logger.tsx", "medium", "乐观 reducer 写 sessionStorage（变体 B）。",
     '''import { useOptimistic, startTransition } from "react";

export function Logger({ lines }: { lines: string[] }) {
  const [optimistic, addLine] = useOptimistic(lines, (current, next: string) => {
    sessionStorage.setItem("last-line", next);
    return [...current, next];
  });

  function log() {
    startTransition(async () => {
      addLine("entry");
      await fetch("/api/log", { method: "POST" });
    });
  }

  return <button onClick={log}>{optimistic.length} lines</button>;
}
'''),
    ("082", "compliant", "R-012", "Logger.tsx", "medium", "纯乐观 reducer（变体 B）。",
     '''import { useOptimistic, startTransition } from "react";

export function Logger({ lines }: { lines: string[] }) {
  const [optimistic, addLine] = useOptimistic(lines, (current, next: string) => [
    ...current,
    next,
  ]);

  function log() {
    startTransition(async () => {
      addLine("entry");
      await fetch("/api/log", { method: "POST" });
    });
  }

  return <button onClick={log}>{optimistic.length} lines</button>;
}
'''),
    ("083", "violation", "R-003", "Reporter.tsx", "medium", "addEventListener 无清理（变体 B）。",
     '''import { useEffect, useState } from "react";

export function Reporter({ target }: { target: EventTarget }) {
  const [events, setEvents] = useState(0);

  useEffect(() => {
    const handler = () => setEvents((n) => n + 1);
    target.addEventListener("report", handler);
    console.log("reporter attached");
  }, [target]);

  return <p>events: {events}</p>;
}
'''),
    ("084", "compliant", "R-003", "Reporter.tsx", "medium", "addEventListener 带清理（变体 B）。",
     '''import { useEffect, useState } from "react";

export function Reporter({ target }: { target: EventTarget }) {
  const [events, setEvents] = useState(0);

  useEffect(() => {
    const handler = () => setEvents((n) => n + 1);
    target.addEventListener("report", handler);
    return () => target.removeEventListener("report", handler);
  }, [target]);

  return <p>events: {events}</p>;
}
'''),
    ("085", "violation", "R-004", "Gate.tsx", "medium", "Hook 在条件分支内（变体 B）。",
     '''import { useState } from "react";

export function Gate({ locked }: { locked: boolean }) {
  if (locked) {
    const [attempts, setAttempts] = useState(0);
    return <p>locked ({attempts})</p>;
  }
  return <p>open</p>;
}
'''),
    ("086", "compliant", "R-004", "Gate.tsx", "medium", "Hook 在条件分支外（变体 B）。",
     '''import { useState } from "react";

export function Gate({ locked }: { locked: boolean }) {
  const [attempts, setAttempts] = useState(0);

  if (locked) {
    return <p>locked ({attempts})</p>;
  }
  return <p>open</p>;
}
'''),
    ("087", "violation", "R-002", "VoteForm.tsx", "medium", "手动表单（变体 C）。",
     '''import { useState } from "react";

export function VoteForm() {
  const [choice, setChoice] = useState("");

  function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    void fetch("/api/vote", { method: "POST", body: choice });
  }

  return (
    <form onSubmit={submit}>
      <input value={choice} onChange={(e) => setChoice(e.target.value)} />
      <button type="submit">Vote</button>
    </form>
  );
}
'''),
    ("088", "compliant", "R-002", "VoteForm.tsx", "medium", "action prop（变体 C）。",
     '''import { useActionState } from "react";

async function vote(_prev: string, formData: FormData): Promise<string> {
  const choice = String(formData.get("choice") ?? "");
  await fetch("/api/vote", { method: "POST", body: choice });
  return choice;
}

export function VoteForm() {
  const [choice, formAction, isPending] = useActionState(vote, "");

  return (
    <form action={formAction}>
      <input name="choice" disabled={isPending} />
      <button type="submit" disabled={isPending}>Vote</button>
      <p>{choice}</p>
    </form>
  );
}
'''),
    ("089", "violation", "R-008", "GeoHint.tsx", "hard", "SSR use(browser()) 无边界（变体 B）。",
     '''import { use } from "react";

declare function browserRegion(): Promise<string>;

export function GeoHint() {
  const region = use(browserRegion());
  return <span>{region}</span>;
}
'''),
    ("090", "compliant", "R-008", "GeoHint.tsx", "hard", "SSR use(browser()) 有边界（变体 B）。",
     '''import { use, Suspense } from "react";

declare function browserRegion(): Promise<string>;

function Region() {
  const region = use(browserRegion());
  return <span>{region}</span>;
}

export function GeoHint() {
  return (
    <Suspense fallback="...">
      <Region />
    </Suspense>
  );
}
'''),
    ("091", "violation", "R-001", "Feed.tsx", "medium", "useEffect 取数（变体 C）。",
     '''import { useEffect, useState } from "react";

export function Feed({ cursor }: { cursor: string }) {
  const [items, setItems] = useState<unknown[]>([]);

  useEffect(() => {
    fetch(`/api/feed?cursor=${cursor}`)
      .then((r) => r.json())
      .then((d) => setItems(d.items));
  }, [cursor]);

  return <ul>{items.map((i, k) => <li key={k}>{String(i)}</li>)}</ul>;
}
'''),
    ("092", "compliant", "R-001", "Feed.tsx", "medium", "use() + 缓存（变体 C）。",
     '''import { use, Suspense } from "react";

const cache = new Map<string, Promise<{ items: unknown[] }>>();

function getFeed(cursor: string): Promise<{ items: unknown[] }> {
  if (!cache.has(cursor)) cache.set(cursor, fetch(`/api/feed?cursor=${cursor}`).then((r) => r.json()));
  return cache.get(cursor)!;
}

function List({ cursor }: { cursor: string }) {
  const data = use(getFeed(cursor));
  return <ul>{data.items.map((i, k) => <li key={k}>{String(i)}</li>)}</ul>;
}

export function Feed({ cursor }: { cursor: string }) {
  return (
    <Suspense fallback="loading">
      <List cursor={cursor} />
    </Suspense>
  );
}
'''),
    ("093", "violation", "R-005", "Bookmark.tsx", "medium", "手动乐观收藏（变体 C）。",
     '''import { useState } from "react";

export function Bookmark({ marked }: { marked: boolean }) {
  const [state, setState] = useState(marked);

  function toggle() {
    setState(!state);
    void fetch("/api/bookmark", { method: "POST" });
  }

  return <button onClick={toggle}>{state ? "Marked" : "Mark"}</button>;
}
'''),
    ("094", "compliant", "R-005", "Bookmark.tsx", "medium", "useOptimistic 收藏（变体 C）。",
     '''import { useOptimistic, startTransition } from "react";

export function Bookmark({ marked }: { marked: boolean }) {
  const [optimistic, toggleMark] = useOptimistic(marked);

  function toggle() {
    startTransition(() => {
      toggleMark(!optimistic);
      void fetch("/api/bookmark", { method: "POST" });
    });
  }

  return <button onClick={toggle}>{optimistic ? "Marked" : "Mark"}</button>;
}
'''),
    ("095", "violation", "R-007", "Profile.tsx", "medium", "use(profileFetch(id)) 未缓存（变体 C）。",
     '''import { use } from "react";

type Profile = { handle: string };

export function Profile({ id }: { id: string }) {
  const profile = use(profileFetch(id));
  return <p>@{profile.handle}</p>;
}

async function profileFetch(id: string): Promise<Profile> {
  const res = await fetch(`/api/profile/${id}`);
  return res.json();
}
'''),
    ("096", "compliant", "R-007", "Profile.tsx", "medium", "键控缓存 use（变体 C）。",
     '''import { use } from "react";

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
'''),
    ("097", "violation", "R-006", "cart.ts", "easy", "use() 在 helper（变体 C）。",
     '''import { use } from "react";
import { CartContext } from "./cart-context";

export function cartTotal() {
  const cart = use(CartContext);
  return cart.items.reduce((sum, i) => sum + i.price, 0);
}
'''),
    ("098", "compliant", "R-006", "cart.ts", "easy", "use() 在 useCartTotal Hook（变体 C）。",
     '''import { use } from "react";
import { CartContext } from "./cart-context";

export function useCartTotal() {
  const cart = use(CartContext);
  return cart.items.reduce((sum, i) => sum + i.price, 0);
}
'''),
    ("099", "violation", "R-010", "FollowChip.tsx", "medium", "乐观 setter 在渲染期（变体 C）。",
     '''import { useOptimistic } from "react";

export function FollowChip({ following }: { following: boolean }) {
  const [optimistic, toggleFollow] = useOptimistic(following);

  toggleFollow(!following);

  return <span>{optimistic ? "Following" : "Follow"}</span>;
}
'''),
    ("100", "compliant", "R-010", "FollowChip.tsx", "medium", "乐观 setter 在 Action（变体 C）。",
     '''import { useOptimistic, startTransition } from "react";

export function FollowChip({ following }: { following: boolean }) {
  const [optimistic, toggleFollow] = useOptimistic(following);

  function toggle() {
    startTransition(() => {
      toggleFollow(!optimistic);
      void fetch("/api/follow", { method: "POST" });
    });
  }

  return <button onClick={toggle}>{optimistic ? "Following" : "Follow"}</button>;
}
'''),
    ("101", "violation", "R-011", "Inviter.tsx", "medium", "dispatch 在 promise 回调（变体 C）。",
     '''import { useActionState } from "react";

async function addMember(prev: string | null, email: string): Promise<string | null> {
  const res = await fetch("/api/members", { method: "POST", body: email });
  return res.ok ? email : prev;
}

export function Inviter() {
  const [member, dispatchAction, isPending] = useActionState(addMember, null);

  function invite() {
    queueMicrotask(() => dispatchAction("new-member@example.com"));
  }

  return (
    <button onClick={invite} disabled={isPending}>Invite</button>
  );
}
'''),
    ("102", "compliant", "R-011", "Inviter.tsx", "medium", "dispatch 在 Action（变体 C）。",
     '''import { useActionState, startTransition } from "react";

async function addMember(prev: string | null, email: string): Promise<string | null> {
  const res = await fetch("/api/members", { method: "POST", body: email });
  return res.ok ? email : prev;
}

export function Inviter() {
  const [member, dispatchAction, isPending] = useActionState(addMember, null);

  function invite() {
    startTransition(() => {
      dispatchAction("new-member@example.com");
    });
  }

  return (
    <button onClick={invite} disabled={isPending}>Invite</button>
  );
}
'''),
    ("103", "violation", "R-012", "Undo.tsx", "medium", "乐观 updater 引用全局配置（变体 C）。",
     '''import { useOptimistic, startTransition } from "react";

import { MAX_ITEMS } from "./config";

export function Undo({ entries }: { entries: string[] }) {
  const [list, push] = useOptimistic(entries, (current, next: string) => {
    if (current.length >= MAX_ITEMS) return current;
    return [...current, next];
  });

  function add() {
    startTransition(() => push("item"));
  }

  return <button onClick={add}>{list.length} entries</button>;
}
'''),
    ("104", "compliant", "R-012", "Undo.tsx", "medium", "纯乐观 updater（变体 C）。",
     '''import { useOptimistic, startTransition } from "react";

export function Undo({ entries }: { entries: string[] }) {
  const [list, push] = useOptimistic(entries, (current, next: string) => [...current, next]);

  function add() {
    startTransition(() => push("item"));
  }

  return <button onClick={add}>{list.length} entries</button>;
}
'''),
]


def main() -> None:
    rr = ROOT / "bench" / "cases" / "react19"
    ab = ROOT / "bench" / "cases" / "airbnb"
    asv = ROOT / "bench" / "cases" / "asvs"
    ag = ROOT / "bench" / "cases" / "agents-sdk"

    n = 0
    for suffix, verdict, rule, fname, diff, note, code in REACT_VARIANTS:
        cid = f"TS-{suffix}"
        w(rr, cid, verdict, rule, fname, diff, note, code)
        n += 1

    # airbnb 12（JS-011..022）
    for i, (mod, fn) in enumerate([("inventory", "listItems"), ("catalog", "findItems"), ("audit", "logItems"), ("orderbook", "matchOrders")]):
        cid = f"JS-{11 + i:03d}"
        w(ab, cid, "violation", "airbnb-002", f"{mod}.js", "easy",
          f"连续访问对象多个属性而未解构（变体 {i+1}），违反 airbnb-002。",
          f'''// bad: repeated property access (variant {i+1})
export function {fn}(order) {{
  const pair = `${{order.symbol}}/${{order.quote}}`;
  const amount = order.amount;
  return {{ pair, amount }};
}}
''')
        n += 1
        cid = f"JS-{17 + i:03d}"
        w(ab, cid, "compliant", "airbnb-002", f"{mod}.js", "easy",
          f"对象解构取多属性（变体 {i+1}），符合 airbnb-002。",
          f'''// good: object destructuring (variant {i+1})
export function {fn}(order) {{
  const {{ symbol, quote, amount }} = order;
  return {{ pair: `${{symbol}}/${{quote}}`, amount }};
}}
''')
        n += 1

    for i, (mod, ev) in enumerate([("telemetry", "emit"), ("webhooks", "dispatch"), ("audit", "record"), ("sync", "push")]):
        cid = f"JS-{21 + i:03d}"
        w(ab, cid, "violation", "airbnb-005", f"{mod}.js", "easy",
          f"匿名内联回调用 function 记法（变体 {i+1}），违反 airbnb-005。",
          f'''// bad: function expression callback (variant {i+1})
queue.subscribe(function (event) {{
  {ev}(event.type, event.payload);
}});
''')
        n += 1
        cid = f"JS-{27 + i:03d}"
        w(ab, cid, "compliant", "airbnb-005", f"{mod}.js", "easy",
          f"内联回调用箭头函数（变体 {i+1}），符合 airbnb-005。",
          f'''// good: arrow function callback (variant {i+1})
queue.subscribe((event) => {{
  {ev}(event.type, event.payload);
}});
''')
        n += 1

    for i, mod in enumerate(["i18n", "theme", "report", "exporter"]):
        cid = f"JS-{31 + i:03d}"
        w(ab, cid, "violation", "airbnb-006", f"{mod}.js", "easy",
          f"字符串用双引号（变体 {i+1}），违反 airbnb-006。",
          '''// bad: double quotes
export const FALLBACK = "unknown";
export const KIND = "system";
''')
        n += 1
        cid = f"JS-{37 + i:03d}"
        w(ab, cid, "compliant", "airbnb-006", f"{mod}.js", "easy",
          f"字符串用单引号（变体 {i+1}），符合 airbnb-006。",
          '''// good: single quotes
export const FALLBACK = 'unknown';
export const KIND = 'system';
''')
        n += 1

    # asvs 12（PY-125..136）
    asv_cases = [
        ("PY-125", "violation", "asvs-V6.2.9", "signup.py", "easy", "前端 maxlength=12（变体）。",
         '''@app.post("/signup")
def signup(email: str = Form(...), password: str = Form(max_length=12)):
    return create_account(email, password)
'''),
        ("PY-126", "compliant", "asvs-V6.2.9", "signup.py", "easy", "允许 72 字符（变体）。",
         '''@app.post("/signup")
def signup(email: str = Form(...), password: str = Form(max_length=72)):
    return create_account(email, password)
'''),
        ("PY-127", "violation", "asvs-V6.2.12", "changepw.py", "medium", "改密不做泄露检查（变体）。",
         '''@app.post("/change-password")
def change_password(user=Depends(current_user), new: str = Form(...)):
    set_password(user, new)
    return {"ok": True}
'''),
        ("PY-128", "compliant", "asvs-V6.2.12", "changepw.py", "medium", "改密对照泄露库（变体）。",
         '''@app.post("/change-password")
def change_password(user=Depends(current_user), new: str = Form(...)):
    if is_breached(new):
        raise HTTPException(status_code=400, detail="breached password")
    set_password(user, new)
    return {"ok": True}
'''),
        ("PY-129", "violation", "asvs-V1.1.2", "preview.py", "medium", "插值未编码（变体）。",
         '''def render_preview(title: str, body: str) -> str:
    return f"<article><h2>{title}</h2>{body}</article>"
'''),
        ("PY-130", "compliant", "asvs-V1.1.2", "preview.py", "medium", "html.escape（变体）。",
         '''import html

def render_preview(title: str, body: str) -> str:
    return f"<article><h2>{html.escape(title)}</h2>{html.escape(body)}</article>"
'''),
        ("PY-131", "violation", "asvs-V3.3.3", "auth_cookie.py", "easy", "无 __Host- 前缀（变体）。",
         '''resp.set_cookie("sid", token, secure=True, httponly=True, samesite="lax")
'''),
        ("PY-132", "compliant", "asvs-V3.3.3", "auth_cookie.py", "easy", "__Host- 前缀（变体）。",
         '''resp.set_cookie("__Host-sid", token, secure=True, httponly=True, samesite="lax", path="/")
'''),
        ("PY-133", "violation", "asvs-V7.3.1", "api_session.py", "medium", "只验签名不校验时效（变体）。",
         '''def authorize(request) -> bool:
    return verify_signature(request.cookies.get("sid"))
'''),
        ("PY-134", "compliant", "asvs-V7.3.1", "api_session.py", "medium", "签名 + 时效（变体）。",
         '''def authorize(request) -> bool:
    session = load_session(request.cookies.get("sid"))
    if session is None or session.expired():
        return False
    return verify_signature(request.cookies.get("sid"))
'''),
        ("PY-135", "violation", "asvs-V7.4.5", "org_admin.py", "medium", "停用不吊销会话（变体）。",
         '''@app.post("/org/members/{member_id}/disable")
def disable_member(member_id: str):
    db.set_member_state(member_id, active=False)
    return {"ok": True}
'''),
        ("PY-136", "compliant", "asvs-V7.4.5", "org_admin.py", "medium", "停用并吊销会话（变体）。",
         '''@app.post("/org/members/{member_id}/disable")
def disable_member(member_id: str):
    db.set_member_state(member_id, active=False)
    db.revoke_sessions(member_id)
    return {"ok": True}
'''),
    ]
    for cid, verdict, rule, fname, diff, note, code in asv_cases:
        w(asv, cid, verdict, rule, fname, diff, note, code)
        n += 1

    # agents-sdk 12（PY-017..028）
    ag_cases = [
        ("PY-017", "violation", "agents-001", "extractor.py", "medium", "无 output_type（变体）。",
         '''from agents import Agent

extractor = Agent(
    name="Extractor",
    instructions="Extract entities as JSON array with fields name and type.",
)
'''),
        ("PY-018", "compliant", "agents-001", "extractor.py", "medium", "output_type 设置（变体）。",
         '''from pydantic import BaseModel
from agents import Agent


class Entities(BaseModel):
    entities: list[dict]


extractor = Agent(
    name="Extractor",
    instructions="Extract entities from the text.",
    output_type=Entities,
)
'''),
        ("PY-019", "violation", "agents-002", "planner.py", "medium", "拼好后未 return（变体）。",
         '''from agents import Agent

def dynamic_prompt(agent, context) -> str:
    prompt = f"Plan for {context.goal}. Budget: {context.budget}"
'''),
        ("PY-020", "compliant", "agents-002", "planner.py", "medium", "返回 prompt（变体）。",
         '''from agents import Agent

def dynamic_prompt(agent, context) -> str:
    return f"Plan for {context.goal}. Budget: {context.budget}"
'''),
        ("PY-021", "violation", "agents-003", "sentinel.py", "medium", "筛查在 agent 之后（变体）。",
         '''from agents import Agent

agent = Agent(name="Helper", instructions="Answer questions.")

async def handle(text: str) -> str:
    out = await run_agent(agent, text)
    await policy_screen(text)
    return out
'''),
        ("PY-022", "compliant", "agents-003", "sentinel.py", "medium", "input_guardrails（变体）。",
         '''from agents import Agent, InputGuardrail

screen = Agent(name="Screen", instructions="Screen the input.")
guardrail = InputGuardrail(guardrail_agent=screen)

agent = Agent(name="Helper", instructions="Answer questions.", input_guardrails=[guardrail])
'''),
        ("PY-023", "violation", "agents-004", "cost_guard.py", "medium", "并行模式（变体）。",
         '''from agents import Agent, InputGuardrail

guardrail = InputGuardrail(guardrail_agent=make_gatekeeper(), run_in_parallel=True)

expensive = Agent(name="Expensive", instructions="...", input_guardrails=[guardrail])
'''),
        ("PY-024", "compliant", "agents-004", "cost_guard.py", "medium", "阻塞模式（变体）。",
         '''from agents import Agent, InputGuardrail

guardrail = InputGuardrail(guardrail_agent=make_gatekeeper(), run_in_parallel=False)

expensive = Agent(name="Expensive", instructions="...", input_guardrails=[guardrail])
'''),
        ("PY-025", "violation", "agents-005", "translate.py", "easy", "无 docstring（变体）。",
         '''from agents import function_tool

@function_tool
def translate(text: str, target: str) -> str:
    return translate_api(text, target)
'''),
        ("PY-026", "compliant", "agents-005", "translate.py", "easy", "带 docstring（变体）。",
         '''from agents import function_tool

@function_tool
def translate(text: str, target: str) -> str:
    """Translate text into the target language."""

    return translate_api(text, target)
'''),
        ("PY-027", "violation", "agents-006", "fetcher_tool.py", "medium", "无错误处理（变体）。",
         '''def invoke(ctx, arguments: str) -> str:
    return fetch(json.loads(arguments)["url"])
'''),
        ("PY-028", "compliant", "agents-006", "fetcher_tool.py", "medium", "错误处理（变体）。",
         '''def invoke(ctx, arguments: str) -> str:
    try:
        return fetch(json.loads(arguments)["url"])
    except Exception as e:
        return f"fetch failed: {e}"
'''),
    ]
    for cid, verdict, rule, fname, diff, note, code in ag_cases:
        w(ag, cid, verdict, rule, fname, diff, note, code)
        n += 1

    print(f"batch3: {n} cases")


if __name__ == "__main__":
    main()
