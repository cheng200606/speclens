from agents import Agent
from agents.run import ModelInputData

def prepare_input(agent, input_items) -> ModelInputData:
    return ModelInputData(input=input_items)
