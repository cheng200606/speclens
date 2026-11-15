from agents import Agent, handoff

billing = Agent(name="Billing", instructions="Handle billing questions.")
refunds = Agent(name="Refunds", instructions="Handle refund requests.")

triage = Agent(
    name="Triage",
    instructions="Route billing or refunds questions to the right agent.",
    handoffs=[handoff(billing)],
)
