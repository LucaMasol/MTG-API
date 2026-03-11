import os
import httpx
from dotenv import load_dotenv

from app.database import Base, engine, SessionLocal
from app.models import Tournament, Deck

load_dotenv()

SPICERACK_API_KEY = os.getenv("SPICERACK_API_KEY")
SPICERACK_EXPORT_URL = "https://api.spicerack.gg/api/export-decklists/"



def fetch_pauper_tournaments(days: int = 180) -> list[dict]:
  if not SPICERACK_API_KEY:
    raise RuntimeError("SPICERACK_API_KEY is not set")

  params = {
    "num_days": days,
    "event_format": "Pauper",
    "decklist_as_text": "true", # Doesn't seem to do anything despite it being in the documentation
  }

  # Auth API key
  headers = {
    "X-API-Key": SPICERACK_API_KEY
  }

  with httpx.Client(timeout=60.0) as client:
    response = client.get(SPICERACK_EXPORT_URL, params=params, headers=headers)

  if response.status_code != 200:
    raise RuntimeError(
      f"Spicerack request failed: {response.status_code} {response.text}"
    )

  return response.json()


def import_pauper_tournaments(days: int = 180) -> None:
  tournaments_data = fetch_pauper_tournaments(days=days)

  Base.metadata.create_all(bind=engine)

  session = SessionLocal()

  try:
    imported_count = 0
    skipped_count = 0
    
    for tournament_data in tournaments_data:
      tid = str(tournament_data["TID"])

      existing_tournament = session.get(Tournament, tid)

      # If tournament is already in DB, skip
      if existing_tournament:
        skipped_count += 1
        continue

      existing_tournament = Tournament(
        tid=tid,
        tournament_name=tournament_data.get("tournamentName", ""),
        format=tournament_data.get("format", ""),
        players=tournament_data.get("players", 0),
        start_date=tournament_data.get("startDate", 0),
        swiss_rounds=tournament_data.get("swissRounds", 0),
      )
      session.add(existing_tournament)

      standings = tournament_data.get("standings", [])

      for i, standing in enumerate(standings, start=1):
        decklist = standing.get("decklist")
        if not decklist:
          continue

        # Add deck to DB. 
        # Decklist will have to be added via process_moxfield_decklists script
        # Archetype will have to be added via classify_decks script
        deck = Deck(
          tournament_id=tid,
          deck_id=i,
          name=standing.get("name"),
          moxfield_decklist=decklist,
          wins_swiss=standing.get("winsSwiss", 0),
          losses_swiss=standing.get("lossesSwiss", 0),
          draws=standing.get("draws", 0),
          bracket_wins=standing.get("winsBracket", 0),
          bracket_losses=standing.get("lossesBracket", 0),
          decklist_processed=False,
        )
        session.add(deck)
        imported_count += 1

    session.commit()
    if imported_count:
      print(f"Imported {imported_count} tournaments")
    if skipped_count:
      print(f"Skipped {skipped_count} tournaments that are already in database")


  except Exception:
    session.rollback()
    raise
  finally:
    session.close()


if __name__ == "__main__":
  import_pauper_tournaments(days=30)