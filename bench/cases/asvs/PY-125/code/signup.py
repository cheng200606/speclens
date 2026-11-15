@app.post("/signup")
def signup(email: str = Form(...), password: str = Form(max_length=12)):
    return create_account(email, password)
