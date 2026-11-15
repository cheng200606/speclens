@app.post("/forgot/confirm")
def forgot_confirm(email: str = Form(...), code: str = Form(...), new: str = Form(...)):
    if check_email_code(email, code):
        set_password(email, new)
        login(email)
        return {"ok": True}
    raise HTTPException(status_code=400)
