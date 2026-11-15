@app.post("/upload")
async def upload(request: Request):
    body = await request.body()
    save(request.headers["x-filename"], body)
    return {"ok": True}
