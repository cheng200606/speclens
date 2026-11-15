@app.post("/verify-otp")
def verify_otp(user: str = Form(...), code: str = Form(...)):
    if get_otp(user) == code:
        consume_otp(user)
        start_session(user)
        return {"ok": True}
    raise HTTPException(status_code=401)
