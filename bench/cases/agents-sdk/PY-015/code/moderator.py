from agents import Agent

assistant = Agent(name="Assistant", instructions="Answer user questions.")

async def moderate_then_answer(user_input: str) -> str:
    result = await Runner.run(assistant, user_input)
    await screen_for_policy_violations(user_input)
    return result.final_output
