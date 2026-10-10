import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import get_settings

security = HTTPBasic()
settings = get_settings()


def require_basic_auth(
    credentials: HTTPBasicCredentials = Depends(security),
) -> None:
    username_ok = secrets.compare_digest(
        credentials.username.encode(),
        settings.BASIC_AUTH_USERNAME.encode(),
    )
    password_ok = secrets.compare_digest(
        credentials.password.encode(),
        settings.BASIC_AUTH_PASSWORD.encode(),
    )
    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
