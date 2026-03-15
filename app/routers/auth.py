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
  description=(
    "Create a user account with an email address and password. "
    "On success, the API returns a newly generated API key. "
    "This API key is shown only once, so the client should store it securely."
  ),
  responses={
    201: {
      "description": "User created successfully",
      "content": {
        "application/json": {
          "example": {
            "message": "User created. Store this API key securely, as it will not be shown again.",
            "api_key": "mtg_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
          }
        }
      },
    },
    409: {
      "description": "Email already registered",
      "content": {
        "application/json": {
          "example": {
            "detail": "Email already registered"
          }
        }
      },
    },
    422: {
      "description": "Validation error, such as invalid email or password too short",
      "content": {
        "application/json": {
          "example": {
            "detail": [
              {
                "loc": ["body", "password"],
                "msg": "String should have at least 8 characters",
                "type": "string_too_short"
              }
            ]
          }
        }
      },
    },
  },
)
def signup_route(payload: SignupRequest, db: Session = Depends(get_db)):
  """
  Example request body:

  {
    "email": "test@example.com",
    "password": "securepassword123"
  }
  """
  return signup(payload, db)