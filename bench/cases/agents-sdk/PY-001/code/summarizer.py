from agents import Agent, Runner

summarizer = Agent(
    name="Summarizer",
    instructions="Summarize the article as JSON with keys title and points.",
)

async def summarize(article: str) -> dict:
    result = await Runner.run(summarizer, article)
    import json
    return json.loads(result.final_output)
