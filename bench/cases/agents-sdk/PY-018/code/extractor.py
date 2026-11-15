from pydantic import BaseModel
from agents import Agent


class Entities(BaseModel):
    entities: list[dict]


extractor = Agent(
    name="Extractor",
    instructions="Extract entities from the text.",
    output_type=Entities,
)
