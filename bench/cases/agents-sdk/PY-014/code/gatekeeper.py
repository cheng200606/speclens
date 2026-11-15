from agents import Agent, InputGuardrail

gatekeeper = Agent(name="Gatekeeper", instructions="Block policy-violating input.")

guardrail = InputGuardrail(guardrail_agent=gatekeeper, run_in_parallel=False)

assistant = Agent(
    name="Assistant",
    instructions="Expensive assistant model.",
    input_guardrails=[guardrail],
)
