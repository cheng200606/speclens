def render_comment(request):
    comment = request.args["comment"]
    return f"<div class=comment>{comment}</div>"
