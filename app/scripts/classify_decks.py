from app.database import SessionLocal
from app.models import Deck, DecklistCard
from app.services.deck_analysis import (
    load_archetype_signatures,
    predict_archetype_from_scores,
    score_deck_against_signatures,
)

ROGUE_THRESHOLD = 3

# Score the deck against the top-played archetypes.
# If all scores are low, label it a 'Rogue' deck.
def classify_deck(
  deck_cards: set[str],
  archetype_signatures: dict[str, set[str]],
  rogue_threshold: int = ROGUE_THRESHOLD,
) -> tuple[str, dict[str, int]]:
  scored = score_deck_against_signatures(deck_cards, archetype_signatures)
  predicted_archetype, _ = predict_archetype_from_scores(
    scored,
    rogue_threshold=rogue_threshold,
  )

  flat_scores = {
    archetype: data["score"]
    for archetype, data in scored.items()
  }

  return predicted_archetype, flat_scores


def classify_all_processed_decks(overwrite: bool = False) -> None:
  archetype_signatures = load_archetype_signatures()

  session = SessionLocal()
  updated_count = 0
  deleted_count = 0

  try:
    query = session.query(Deck).filter(Deck.decklist_processed.is_(True))
    if not overwrite:
      query = query.filter(Deck.archetype.is_(None))

    decks = query.all()
    print(f"{len(decks)} decks to label with archetypes")

    for deck in decks:
      deck_cards_rows = session.query(DecklistCard.card_name).filter(
        DecklistCard.tournament_id == deck.tournament_id,
        DecklistCard.deck_id == deck.deck_id,
      ).all()

      deck_cards = {row[0].strip() for row in deck_cards_rows if row[0]}

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