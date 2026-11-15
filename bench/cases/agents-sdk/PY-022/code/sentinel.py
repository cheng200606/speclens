from agents import Agent, InputGuardrail

screen = Agent(name="Screen", instructions="Screen the input.")
guardrail = InputGuardrail(guardrail_agent=screen)

agent = Agent(name="Helper", instructions="Answer questions.", input_guardrails=[guardrail])
