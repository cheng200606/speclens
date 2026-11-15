@app.post("/admin/lockout/{user_id}")
def lockout(user_id: str):
    db.update_user(user_id, disabled=True)
    db.revoke_sessions(user_id)
    return {"ok": True}
