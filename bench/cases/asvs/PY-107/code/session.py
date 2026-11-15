@app.post("/login")
def login(user: str = Form(...), password: str = Form(...)):
    resp = JSONResponse({"ok": True})
    resp.set_cookie("session", make_session(user), secure=True, httponly=True)
    return resp
