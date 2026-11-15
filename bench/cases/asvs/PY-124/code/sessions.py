@app.get("/me/sessions")
def list_sessions(user=Depends(current_user)):
    return db.active_sessions(user)

@app.post("/me/sessions/revoke")
def revoke_sessions(password: str = Form(...), user=Depends(current_user)):
    if not verify_password(user, password):
        raise HTTPException(status_code=403)
    db.revoke_sessions(user)
    return {"ok": True}
