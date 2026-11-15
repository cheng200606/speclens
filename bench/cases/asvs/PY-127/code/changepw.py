@app.post("/change-password")
def change_password(user=Depends(current_user), new: str = Form(...)):
    set_password(user, new)
    return {"ok": True}
