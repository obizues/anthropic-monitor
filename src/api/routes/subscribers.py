from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr

from subscribers.store import add_subscriber, list_subscribers, remove_subscriber
from subscribers.tokens import decode_unsubscribe_token

router = APIRouter()


class SubscriberIn(BaseModel):
    email: EmailStr
    name: str = ""


@router.get("/", response_class=HTMLResponse)
async def subscribers_page() -> HTMLResponse:
    subs = await list_subscribers()
    rows = "".join(
        f"<tr><td>{s['email']}</td><td>{s['name']}</td><td>{s['added_at']}</td>"
        f"<td><a href='/subscribers/{s['email']}' onclick=\"return confirm('Remove?')\">Remove</a></td></tr>"
        for s in subs
    )
    html = f"""
    <!DOCTYPE html><html><head><title>Subscribers</title>
    <style>body{{font-family:sans-serif;max-width:800px;margin:40px auto;}}
    table{{width:100%;border-collapse:collapse;}}th,td{{padding:8px;border-bottom:1px solid #eee;text-align:left;}}
    input,button{{padding:8px;margin:4px;}}a{{color:#c7522a;}}</style></head>
    <body><h1>Subscribers</h1>
    <form method="post"><input name="email" type="email" placeholder="email@company.com" required>
    <input name="name" placeholder="Name (optional)">
    <button type="submit">Add</button></form>
    <table><tr><th>Email</th><th>Name</th><th>Added</th><th></th></tr>{rows}</table>
    <p><a href="/">← Dashboard</a></p></body></html>
    """
    return HTMLResponse(html)


@router.post("/")
async def add(sub: SubscriberIn) -> dict:
    await add_subscriber(sub.email, sub.name)
    return {"status": "added", "email": sub.email}


@router.delete("/{email}")
async def remove(email: str) -> dict:
    removed = await remove_subscriber(email)
    if not removed:
        raise HTTPException(404, "Subscriber not found")
    return {"status": "removed", "email": email}


@router.get("/unsubscribe", response_class=HTMLResponse, include_in_schema=False)
async def unsubscribe(token: str) -> HTMLResponse:
    email = decode_unsubscribe_token(token)
    if not email:
        return HTMLResponse("<h2>Invalid or expired unsubscribe link.</h2>", status_code=400)
    await remove_subscriber(email)
    return HTMLResponse(f"<h2>You have been unsubscribed.</h2><p>{email} has been removed.</p>")
