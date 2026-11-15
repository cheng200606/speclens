@app.post("/register2")
def register(username: str = Form(...), password: str = Form(max_length=128)):
    save_user(username, password)
    return {"ok": True}
