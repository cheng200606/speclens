import html

def render_comment(request):
    comment = request.args["comment"]
    return f'<div class="comment">{html.escape(comment)}</div>'
