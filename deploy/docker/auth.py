import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from jwt import JWT, jwk_from_dict
from jwt.utils import get_int_from_datetime
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import EmailStr
from pydantic.main import BaseModel
import base64

instance = JWT()
security = HTTPBearer(auto_error=False)
SECRET_KEY = os.environ.get("SECRET_KEY", "mysecret")
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def get_jwk_from_secret(secret: str):
    """Convert a secret string into a JWK object."""
    secret_bytes = secret.encode('utf-8')
    b64_secret = base64.urlsafe_b64encode(secret_bytes).rstrip(b'=').decode('utf-8')
    return jwk_from_dict({"kty": "oct", "k": b64_secret})

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with an expiration."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": get_int_from_datetime(expire)})
    signing_key = get_jwk_from_secret(SECRET_KEY)
    return instance.encode(to_encode, signing_key, alg='HS256')

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Verify the JWT token from the Authorization header."""

    if credentials is None:
        return None
    token = credentials.credentials
    verifying_key = get_jwk_from_secret(SECRET_KEY)
    try:
        payload = instance.decode(token, verifying_key, do_time_check=True, algorithms='HS256')
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_token_dependency(config: Dict):
    """Return the token dependency if JWT is enabled, else a function that returns None."""

    if config.get("security", {}).get("jwt_enabled", False):
        return verify_token
    else:
        return lambda: None


class TokenRequest(BaseModel):
    email: EmailStr