import secrets
import hashlib
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import Header, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import User, ApiKey
from app.database import SessionLocal
from pydantic import BaseModel, EmailStr, Field
from database_helpers import get_db

def generate_api_key() -> str:
  return "mtg_" + secrets.token_urlsafe(32)

def hash_api_key(raw_key: str) -> str:
  return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

def key_prefix(raw_key: str) -> str:
  return raw_key[:12]


pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
  return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
  return pwd_context.verify(password, password_hash)

def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.flush()

    raw_key = generate_api_key()
    api_key = ApiKey(
        user_id=user.id,
        key_prefix=key_prefix(raw_key),
        key_hash=hash_api_key(raw_key),
    )
    db.add(api_key)
    db.commit()
    return SignupResponse(
        message="User created. Store this API key securely, as it will not be shown again.",
        api_key=raw_key,
    )

class SignupRequest(BaseModel):
  email: EmailStr
  password: str = Field(min_length=8, max_length=128)


class SignupResponse(BaseModel):
  message: str
  api_key: str
    



RATE_LIMIT_REQUESTS = 5
RATE_LIMIT_WINDOW_SECONDS = 5
BLOCK_MINUTES = 5

def get_api_key_record(
  x_api_key: str | None = Header(default=None, alias="X-API-Key"),
  db: Session = Depends(get_db),
) -> ApiKey:
  if not x_api_key:
    raise HTTPException(status_code=401, detail="Missing API key")

  hashed = hash_api_key(x_api_key)
  api_key = db.query(ApiKey).filter(ApiKey.key_hash == hashed).first()

  if not api_key:
    raise HTTPException(status_code=401, detail="Invalid API key")

  now = datetime.utcnow()

  if api_key.is_blocked and api_key.blocked_until and api_key.blocked_until > now:
    raise HTTPException(
      status_code=429,
      detail=f"API key temporarily blocked until {api_key.blocked_until.isoformat()} UTC"
    )

  if api_key.blocked_until and api_key.blocked_until <= now:
    api_key.is_blocked = False
    api_key.blocked_until = None
    api_key.request_count = 0
    api_key.window_started_at = now

  window_start = api_key.window_started_at or now
  elapsed = (now - window_start).total_seconds()

  if elapsed > RATE_LIMIT_WINDOW_SECONDS:
    api_key.window_started_at = now
    api_key.request_count = 1
  else:
    api_key.request_count += 1

  if api_key.request_count > RATE_LIMIT_REQUESTS:
    api_key.is_blocked = True
    api_key.blocked_until = now + timedelta(minutes=BLOCK_MINUTES)
    db.commit()
    raise HTTPException(
      status_code=429,
      detail=f"Rate limit exceeded. API key blocked for {BLOCK_MINUTES} minutes."
    )

  db.commit()
  return api_key