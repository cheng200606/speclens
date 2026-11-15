def authorize(request) -> bool:
    return verify_signature(request.cookies.get("sid"))
