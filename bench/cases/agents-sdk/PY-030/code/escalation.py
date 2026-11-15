from agents import Agent, handoff

general = Agent(name="General", instructions="General support.")
billing = Agent(name="Billing", instructions="Billing.")
technical = Agent(name="Technical", instructions="Technical issues.")

support = Agent(
    name="Support",
    handoffs=[handoff(general), handoff(billing), handoff(technical)],
)
