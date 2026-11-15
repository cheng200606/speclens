@app.get("/me")
def me(user=Depends(current_user)):
    return {"name": user.name}
