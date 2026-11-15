from agents import function_tool

@function_tool
def translate(text: str, target: str) -> str:
    return translate_api(text, target)
