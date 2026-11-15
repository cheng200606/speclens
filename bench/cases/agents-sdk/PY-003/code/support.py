from agents import Agent

def build_instructions(agent, context) -> str:
    # 只打印不返回：函数体缺少 return
    print(f"You are helping {context.user_name}. Policy: {context.policy}")

support = Agent(
    name="Support",
    instructions=build_instructions,
)
