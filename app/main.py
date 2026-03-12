from fastapi import FastAPI, APIRouter
from app.routers.auth import router as auth_router
from app.routers.meta import router as meta_router
from app.routers.user_decks import router as user_decks_router

app = FastAPI(
  title="MTG Meta Analytics API",
  description="API for analyzing Magic: The Gathering decks and metagame data",
  version="0.3"
)

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(meta_router)
api_v1_router.include_router(user_decks_router)

app.include_router(api_v1_router)

@app.get("/")
def root():
  return {"message": "Server is running. See http://127.0.0.1:8000/docs for documentation."}
