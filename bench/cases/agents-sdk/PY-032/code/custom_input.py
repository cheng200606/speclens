from agents import RunConfig
from agents.run import ModelInputData

def make_input(agent, items):
    return ModelInputData(input=items)
