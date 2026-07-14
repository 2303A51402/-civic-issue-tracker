import os

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

# Reuses SECRET_KEY as the promotion password — set once as an env var on Render,
# never committed to git. Anyone without this key cannot promote an account.
PROMOTE_KEY = os.getenv("SECRET_KEY", "change-this-secret-in-production")


class PromoteRequest(BaseModel):
    email: EmailStr
    key: str


@router.post("/signup", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def signup(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=models.UserRole.citizen,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return schemas.Token(access_token=token, user=user)


@router.post("/promote-to-admin", response_model=schemas.UserOut)
def promote_to_admin(payload: PromoteRequest, db: Session = Depends(get_db)):
    """One-time-use utility for remote deployments (e.g. Render free tier with no
    shell access). Requires the same SECRET_KEY set in your environment variables,
    so it's safe as long as that key stays private."""
    if payload.key != PROMOTE_KEY:
        raise HTTPException(status_code=403, detail="Invalid key")

    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user with that email")

    user.role = models.UserRole.admin
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return schemas.Token(access_token=token, user=user)