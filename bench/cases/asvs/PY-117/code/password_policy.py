from datetime import datetime, timedelta

def needs_rotation(user) -> bool:
    return datetime.now() - user.password_changed_at > timedelta(days=90)
