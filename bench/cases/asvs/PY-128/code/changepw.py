@app.post("/change-password")
def change_password(user=Depends(current_user), new: str = Form(...)):
    if is_breached(new):
        raise HTTPException(status_code=400, detail="breached password")
    set_password(user, new)
    return {"ok": True}
