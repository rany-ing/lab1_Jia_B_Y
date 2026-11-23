from secrets import token_urlsafe

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

hasher = PasswordHasher()
_dummy_hash = hasher.hash(token_urlsafe(32))


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        hasher.verify(password_hash or _dummy_hash, password)
    except (VerificationError, InvalidHashError):
        return False
    return password_hash is not None
