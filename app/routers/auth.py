from fastapi import APIRouter, Depends
from app.services.authentication_and_security import signup, SignupRequest
from sqlalchemy.orm import Session
from app.services.database_helpers import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
  "/signup",
  summary="Create a new user account and obtain your API key",
  description="Input user email and password as parameters. Password must be at least 8 characters long."
)
def signup_route(payload: SignupRequest, db: Session = Depends(get_db)):
  return signup(payload, db)