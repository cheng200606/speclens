from fastapi import FastAPI, Form

app = FastAPI()

@app.post("/register")
def register(username: str = Form(...), password: str = Form(max_length=20)):
    return save_user(username, password)
