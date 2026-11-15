def invoke(ctx, arguments: str) -> str:
    return fetch(json.loads(arguments)["url"])
