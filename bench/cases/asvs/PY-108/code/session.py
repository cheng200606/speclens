@app.post("/login")
def login(user: str = Form(...), password: str = Form(...)):
    resp = JSONResponse({"ok": True})
    resp.set_cookie("__Host-session", make_session(user), secure=True, httponly=True, path="/")
    return resp
