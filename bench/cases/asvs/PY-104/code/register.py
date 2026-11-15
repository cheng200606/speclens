@app.post("/register2")
def register(username: str = Form(...), password: str = Form(max_length=128)):
    if is_breached(password):
        raise HTTPException(status_code=400, detail="password appears in breach corpus")
    save_user(username, password)
    return {"ok": True}
