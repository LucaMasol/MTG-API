import logging
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI, APIRouter

from app.database import Base, engine

from app.routers.auth import router as auth_router
from app.routers.meta import router as meta_router
from app.routers.user_decks import router as user_decks_router
from app.scripts.spicerack_sync import run_spicerack_sync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
  # Create tables if they do not yet exist
  Base.metadata.create_all(bind=engine)

  scheduler.add_job(
    run_spicerack_sync,
    trigger=IntervalTrigger(hours=6),
    id="spicerack_sync",
    replace_existing=True,
    max_instances=1,
    coalesce=True,
  )
  scheduler.start()
  logger.info("Spicerack sync scheduler started")

  # On startup, fetch the last 240 days of tournaments
  try:
    run_spicerack_sync(days=240)
    logger.info("Initial Spicerack sync completed")
  except Exception:
    logger.exception("Initial Spicerack sync failed. The database may be out of sync.")

  try:
    yield
  finally:
    if scheduler.running:
      scheduler.shutdown()
      logger.info("Spicerack sync scheduler stopped")

app = FastAPI(
  title="MTG Meta Analytics API",
  description="API for analysing Magic: The Gathering decks and metagame data",
  version="1.0",
  lifespan=lifespan,
)

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(meta_router)
api_v1_router.include_router(user_decks_router)

app.include_router(api_v1_router)

@app.get("/")
def root():
  return {"message": "Server is running. See /docs for documentation."}