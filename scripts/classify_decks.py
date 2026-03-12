import json
from pathlib import Path

from app.database import SessionLocal
from app.models import Deck, DecklistCard


SIGNATURES_PATH = Path("data/core_archetype_cards.json")
ROGUE_THRESHOLD = 3

# Signature being the core cards in a deck that make up an archetype
def load_archetype_signatures(path: Path) -> dict[str, set[str]]:
  with path.open("r", encoding="utf-8") as f:
    raw_data = json.load(f)

  return {
    archetype: set(cards)
    for archetype, cards in raw_data.items()
  }

# Score the deck against the top-played archetypes.
# If all scores are low, label it a 'Rogue' deck.
def classify_deck(
  deck_cards: set[str],
  archetype_signatures: dict[str, set[str]],
  rogue_threshold: int = 2
) -> tuple[str, dict[str, int]]:
  scores = {}

  for archetype, signature_cards in archetype_signatures.items():
    score = sum(1 for card in signature_cards if card in deck_cards)
    scores[archetype] = score

  best_archetype = max(scores, key=scores.get)
  best_score = scores[best_archetype]

  if best_score < rogue_threshold:
    return "Rogue", scores

  return best_archetype, scores


def classify_all_processed_decks(overwrite: bool = False) -> None:
  archetype_signatures = load_archetype_signatures(SIGNATURES_PATH)

  session = SessionLocal()
  updated_count = 0
  deleted_count = 0

  try:
    query = session.query(Deck).filter(Deck.decklist_processed == True)
    if not overwrite:
      query = query.filter(Deck.archetype.is_(None))

    decks = query.all()
    print(f"{len(decks)} decks to label with archetypes")

    for deck in decks:
      deck_cards_rows = session.query(DecklistCard.card_name).filter(
        DecklistCard.tournament_id == deck.tournament_id,
        DecklistCard.deck_id == deck.deck_id,
      ).all()

      deck_cards = {row[0] for row in deck_cards_rows}

      if not deck_cards:
        print(f"{deck.tournament_id}-{deck.deck_id}: no cards found, deleting deck")
        session.delete(deck)
        session.commit()
        deleted_count += 1
        continue

      predicted_archetype, scores = classify_deck(
        deck_cards=deck_cards,
        archetype_signatures=archetype_signatures,
        rogue_threshold=ROGUE_THRESHOLD,
      )

      deck.archetype = predicted_archetype
      session.commit()

      best_score = max(scores.values()) if scores else 0
      print(f"{deck.tournament_id}-{deck.deck_id}: {predicted_archetype} (score={best_score})")
      updated_count += 1

  finally:
    session.close()
    if updated_count:
      print(f"Updated {updated_count} decks")
    if deleted_count:
      print(f"Deleted {deleted_count} empty decks")


if __name__ == "__main__":
  classify_all_processed_decks(True)