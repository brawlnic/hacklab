"""vcforge - firma token payload.firma con HMAC-SHA256 (formato VaultCore lab)."""
import base64
import hashlib
import hmac
import json

__version__ = "0.3.1"


def b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def sign(payload_b64: str, secret: str) -> str:
    return b64e(hmac.new(secret.encode(), payload_b64.encode(),
                         hashlib.sha256).digest())


def forge(user: str, role: str, secret: str) -> str:
    """Ritorna il token firmato 'base64(payload).base64(sig)'."""
    payload = b64e(json.dumps({"u": user, "role": role}).encode())
    return f"{payload}.{sign(payload, secret)}"
