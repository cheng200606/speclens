MAX_UPLOAD = 10 * 1024 * 1024

@app.post("/upload")
async def upload(request: Request):
    if int(request.headers.get("content-length", 0)) > MAX_UPLOAD:
        raise HTTPException(status_code=413, detail="file too large")
    body = await request.body()
    save(request.headers["x-filename"], body)
    return {"ok": True}
