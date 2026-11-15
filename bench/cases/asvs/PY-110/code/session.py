@app.middleware("http")
async def check_session(request, call_next):
    token = request.cookies.get("__Host-session")
    session = lookup_session(token)
    if session.idle_seconds > 900 or session.age_seconds > 36000:
        raise HTTPException(status_code=401, detail="session expired")
    request.state.user = session.user
    return await call_next(request)
