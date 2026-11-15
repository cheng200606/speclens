from agents import function_tool

@function_tool
def translate(text: str, target: str) -> str:
    """Translate text into the target language."""

    return translate_api(text, target)
