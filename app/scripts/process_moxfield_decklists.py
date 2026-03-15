import re
import time
from curl_cffi import requests

from app.database import SessionLocal
from app.models import Deck, Card, DecklistCard

MOXFIELD_API_BASE = "https://api.moxfield.com/v2/decks/all"


# Get the deck plaintext ID from a Moxfield link
def extract_moxfield_deck_id(deck_url: str | None) -> str | None:
  if not deck_url:
    return None
  match = re.search(r"moxfield\.com/decks/([^/?#]+)", deck_url or "")
  return match.group(1) if match else None

# Get deck data using Moxfield's API with the deck ID
def fetch_moxfield_deck(deck_id: str) -> dict:
  url = f"{MOXFIELD_API_BASE}/{deck_id}"
  response = requests.get(url, impersonate="chrome", timeout=30)
  response.raise_for_status()
  return response.json()

# May have to require more normalisation in the future.
def normalise_card_name(card_name: str) -> str:
  return card_name.strip()



def extract_cards(deck_json: dict) -> dict[str, dict]:
  """
  Returns dict of deck structure:
  
  {
    "Card Name": {"in_mainboard": x, "in_sideboard": y},
    "Card Name": {"in_mainboard": x, "in_sideboard": y},
    ...
  }
  """
  cards = {}

  # Iterate through cards in the mainboard
  for card in deck_json.get("mainboard", {}).values():
    card_name = normalise_card_name(card["card"]["name"])
    quantity = int(card["quantity"])

    if card_name not in cards:
      cards[card_name] = {"in_mainboard": 0, "in_sideboard": 0}

    cards[card_name]["in_mainboard"] += quantity

  # Iterate through cards in the sideboard
  for card in deck_json.get("sideboard", {}).values():
    card_name = normalise_card_name(card["card"]["name"])
    quantity = int(card["quantity"])

    if card_name not in cards:
      cards[card_name] = {"in_mainboard": 0, "in_sideboard": 0}

    cards[card_name]["in_sideboard"] += quantity

  return cards


def process_unprocessed_decklists() -> None:
  """
  Iterates through every deck entry in the database.
  If a deck is not processed, the decklist is fetched via Moxfield and the list is added to the db.
  Waits 1 second between requests as to not overrequest moxfield
  """

  session = SessionLocal()
  success_count = 0
  error_count = 0

  try:
    query = session.query(Deck).filter(Deck.decklist_processed == False)

    decks = query.all()
    print(f"{len(decks)} unprocessed decks")

    for deck in decks:
      time.sleep(1) # Prevents over-requesting
      deck_key = f"{deck.tournament_id}-{deck.deck_id}"

      moxfield_id = extract_moxfield_deck_id(deck.moxfield_decklist)
      # Delete any entries that do not have a decklist
      if not deck.moxfield_decklist or not moxfield_id:
        print(f"Deleting deck {deck_key}: invalid or missing Moxfield ID.")
        session.delete(deck)
        session.commit()
        continue

      try:
        deck_json = fetch_moxfield_deck(moxfield_id)
        extracted_cards = extract_cards(deck_json)

        # If there are any cards already in the list delete them, shouldn't be the case
        session.query(DecklistCard).filter(
          DecklistCard.tournament_id == deck.tournament_id,
          DecklistCard.deck_id == deck.deck_id,
        ).delete()

        card_names = list(extracted_cards.keys())

        # Cards that have already been added to the Card table
        existing_card_rows = (
          session.query(Card.card_name)
          .filter(Card.card_name.in_(card_names))
          .all()
        )
        existing_card_names = {row[0] for row in existing_card_rows}

        # Add new cards to the Card table
        for card_name in card_names:
          if card_name not in existing_card_names:
            session.add(Card(card_name=card_name))

        session.flush()

        # Add each card in the decklist to the Decklist table
        for card_name, quantities in extracted_cards.items():
          session.add(
            DecklistCard(
              tournament_id=deck.tournament_id,
              deck_id=deck.deck_id,
              card_name=card_name,
              in_mainboard=quantities["in_mainboard"],
              in_sideboard=quantities["in_sideboard"],
            )
          )

        # Success, commit
        deck.decklist_processed = True
        session.commit()
        print(f"Processed {deck_key}")
        success_count += 1

      # Failed, rollback
      except Exception as e:
        session.rollback()
        print(f"Failed {deck_key}: {e}")
        error_count += 1

  finally:
    session.close()
    if success_count:
      print(f"Successfully processed {success_count} decks")
    if error_count:
      print(f"Failed to process {error_count} decks")


if __name__ == "__main__":
  process_unprocessed_decklists()