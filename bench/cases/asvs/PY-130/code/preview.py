import html

def render_preview(title: str, body: str) -> str:
    return f"<article><h2>{html.escape(title)}</h2>{html.escape(body)}</article>"
