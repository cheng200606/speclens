@app.post("/org/members/{member_id}/disable")
def disable_member(member_id: str):
    db.set_member_state(member_id, active=False)
    return {"ok": True}
