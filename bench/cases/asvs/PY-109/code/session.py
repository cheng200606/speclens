@app.middleware("http")
async def check_session(request, call_next):
    token = request.cookies.get("__Host-session")
    user = lookup_session(token)
    request.state.user = user
    return await call_next(request)
