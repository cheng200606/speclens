from agents import Agent


def build_instructions(context, agent) -> str:
    return f"You are helping {context.user_name}. Policy: {context.policy}"


support = Agent(
    name="Support",
    instructions=build_instructions,
)
