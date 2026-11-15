from agents import function_tool

@function_tool
def get_weather(city: str) -> str:
    return f"Weather in {city}: sunny, 24C"
