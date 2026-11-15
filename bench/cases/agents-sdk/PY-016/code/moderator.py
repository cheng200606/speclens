from agents import Agent, InputGuardrail

screen = Agent(name="Screen", instructions="Screen input for policy violations.")

guardrail = InputGuardrail(guardrail_agent=screen)

assistant = Agent(
    name="Assistant",
    instructions="Answer user questions.",
    input_guardrails=[guardrail],
)
