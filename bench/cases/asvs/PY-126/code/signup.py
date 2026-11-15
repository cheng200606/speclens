@app.post("/signup")
def signup(email: str = Form(...), password: str = Form(max_length=72)):
    return create_account(email, password)
