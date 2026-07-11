import base64
import hashlib
import hmac
import json
import time


def _encode(value: dict) -> str:
    raw = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def issue_token(username: str, password: str, expected_username: str, expected_password: str, secret: str, ttl: int) -> str | None:
    if not hmac.compare_digest(username, expected_username) or not hmac.compare_digest(password, expected_password):
        return None
    payload = _encode({"sub": username, "exp": int(time.time()) + ttl})
    signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def validate_token(token: str, secret: str) -> bool:
    try:
        payload, signature = token.split(".", 1)
        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return False
        padded = payload + "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        return int(data.get("exp", 0)) > int(time.time()) and bool(data.get("sub"))
    except (ValueError, KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        return False
