@app.post("/login/otp")
def login_otp(user: str = Form(...), code: str = Form(...)):
    if consume_otp(user, code):
        return {"token": issue_token(user)}
    raise HTTPException(status_code=401)
