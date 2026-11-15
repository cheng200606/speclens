from agents import Agent

def dynamic_prompt(agent, context) -> str:
    return f"Plan for {context.goal}. Budget: {context.budget}"
