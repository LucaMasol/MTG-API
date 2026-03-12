from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.services.authentication_and_security import (
    signup,
    SignupRequest,
    SignupResponse,
)
from app.services.database_helpers import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
  "/signup",
  response_model=SignupResponse,
  status_code=status.HTTP_201_CREATED,
  summary="Create a new user account and obtain an API key",
  description="Register a user with an email and password. Returns a generated API key that is shown only once.",
  responses={
    201: {"description": "User created successfully"},
    409: {"description": "Email already registered"},
  },
)
def signup_route(payload: SignupRequest, db: Session = Depends(get_db)):
  return signup(payload, db)