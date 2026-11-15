from agents import Agent

def dynamic_prompt(agent, context) -> str:
    prompt = f"Plan for {context.goal}. Budget: {context.budget}"
