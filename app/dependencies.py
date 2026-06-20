"""
FastAPI dependencies for guarding routes with JWT auth.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import decode_access_token
from app.models import Recruiter

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_recruiter(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Recruiter:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    email = decode_access_token(token)
    if email is None:
        raise credentials_exception

    recruiter = db.query(Recruiter).filter(Recruiter.email == email).first()
    if recruiter is None:
        raise credentials_exception

    return recruiter
