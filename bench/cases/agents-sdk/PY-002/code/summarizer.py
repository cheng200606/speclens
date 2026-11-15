from pydantic import BaseModel
from agents import Agent, Runner


class Summary(BaseModel):
    title: str
    points: list[str]


summarizer = Agent(
    name="Summarizer",
    instructions="Summarize the article.",
    output_type=Summary,
)

async def summarize(article: str) -> Summary:
    result = await Runner.run(summarizer, article)
    return result.final_output_as(Summary)
