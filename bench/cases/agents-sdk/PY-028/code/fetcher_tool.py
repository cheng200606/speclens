def invoke(ctx, arguments: str) -> str:
    try:
        return fetch(json.loads(arguments)["url"])
    except Exception as e:
        return f"fetch failed: {e}"
