import secrets

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"

def generate_otp() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(6))
