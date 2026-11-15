@app.post("/forgot/confirm")
def forgot_confirm(email: str = Form(...), code: str = Form(...), new: str = Form(...), mfa: str = Form(...)):
    if check_email_code(email, code) and verify_mfa(email, mfa):
        set_password(email, new)
        return {"ok": True, "next": "login"}
    raise HTTPException(status_code=400)
