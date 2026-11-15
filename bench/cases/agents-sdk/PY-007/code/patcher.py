import json
from agents import Agent, FunctionTool


def run_function(ctx, arguments: str) -> str:
    args = json.loads(arguments)
    return f"patched {args['path']}"


tool = FunctionTool(
    name="apply_patch",
    description="Apply a patch to a file.",
    params_json_schema={"type": "object", "properties": {"path": {"type": "string"}}},
    on_invoke_tool=run_function,
    is_enabled=True,
)

patcher = Agent(name="Patcher", tools=[tool])
