from agents import Agent


def dynamic_prompt(context, agent) -> str:
    return f"Plan for {context.goal}. Budget: {context.budget}"
