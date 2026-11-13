import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher

ph = PasswordHasher()


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return ph.verify(password_hash, password)
    except Exception:
        return False


def random_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def expiry(minutes: int) -> datetime:
    return utcnow() + timedelta(minutes=minutes)


def valid_college_email(email: str) -> bool:
    value = email.strip().lower()
    if value.count("@") != 1:
        return False
    local, domain = value.rsplit("@", 1)
    return bool(local) and domain == "iitdh.ac.in"
