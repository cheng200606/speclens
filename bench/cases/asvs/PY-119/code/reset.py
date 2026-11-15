@app.post("/reset-password")
def reset_password(token: str = Form(...), password: str = Form(...)):
    if validate_reset_token(token):
        user = user_from_token(token)
        set_password(user, password)
        start_session(user)
        return {"ok": True}
    raise HTTPException(status_code=400)
