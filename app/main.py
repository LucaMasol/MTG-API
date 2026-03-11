from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
  title="MTG Meta Analytics API",
  description="API for analyzing Magic: The Gathering decks and metagame data",
  version="0.1"
)

@app.get("/")
def root():
  return {"message": "Server is running. Make a GET request to /help for commamnds."}