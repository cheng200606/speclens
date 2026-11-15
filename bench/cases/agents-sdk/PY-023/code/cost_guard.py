from agents import Agent, InputGuardrail

guardrail = InputGuardrail(guardrail_agent=make_gatekeeper(), run_in_parallel=True)

expensive = Agent(name="Expensive", instructions="...", input_guardrails=[guardrail])
