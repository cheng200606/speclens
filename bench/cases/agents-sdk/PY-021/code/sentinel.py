from agents import Agent

agent = Agent(name="Helper", instructions="Answer questions.")

async def handle(text: str) -> str:
    out = await run_agent(agent, text)
    await policy_screen(text)
    return out
