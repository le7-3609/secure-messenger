from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from ..config import settings


class AuthService:
    def hash_password(self, plain: str) -> str:
        '''Returns a bcrypt hash of the plain-text password. Never store the original.'''
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, plain: str, hashed: str) -> bool:
        '''Returns True if the plain password matches the stored bcrypt hash.'''
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    def create_token(self, username: str) -> str:
        '''Creates a signed JWT token containing the username and an expiry time.'''
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.TOKEN_EXPIRE_HOURS)
        return jwt.encode({"sub": username, "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def decode_token(self, token: str) -> Optional[str]:
        '''Decodes a JWT token and returns the username. Returns None if invalid or expired.'''
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload.get("sub")
        except JWTError:
            return None
