def authorize(request) -> bool:
    session = load_session(request.cookies.get("sid"))
    if session is None or session.expired():
        return False
    return verify_signature(request.cookies.get("sid"))
