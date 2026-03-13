from functools import lru_cache
import json
from pathlib import Path
from datetime import datetime

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session, joinedload

from app.models import ApiKey, UserDeck, Deck, DecklistCard, Tournament
from app.services.user_decks import get_owned_deck_or_404



SIGNATURES_PATH = Path("data/core_archetype_cards.json")
DEFAULT_ROGUE_THRESHOLD = 3
TOP_MATCHES_LIMIT = 5


class ArchetypeMatchResponse(BaseModel):
  archetype: str
  score: int
  matched_cards: list[str]


class UserDeckArchetypeAnalysisResponse(BaseModel):
  deck_id: int
  predicted_archetype: str
  best_score: int
  rogue_threshold: int
  card_count: int
  top_matches: list[ArchetypeMatchResponse]
  model_config = ConfigDict(from_attributes=True)


@lru_cache(maxsize=1)
def load_archetype_signatures() -> dict[str, set[str]]:
  with SIGNATURES_PATH.open("r", encoding="utf-8") as f:
    raw_data = json.load(f)

  return {
    archetype: {card.strip() for card in cards if card.strip()}
    for archetype, cards in raw_data.items()
  }


def _normalise_card_name(card_name: str) -> str:
  return card_name.strip()


def extract_user_deck_card_names(deck: UserDeck) -> set[str]:
  """
  Returns distinct card names from the user's deck, ignoring zero-quantity rows.
  Uses both mainboard and sideboard, matching your current tournament classifier style.
  """
  card_names: set[str] = set()

  for card in deck.cards:
    if (card.in_mainboard or 0) <= 0 and (card.in_sideboard or 0) <= 0:
      continue
    card_names.add(_normalise_card_name(card.card_name))

  return card_names


def score_deck_against_signatures(
  deck_cards: set[str],
  archetype_signatures: dict[str, set[str]],
) -> dict[str, dict]:
  """
  Returns:
  {
    "Mono Blue Terror": {
      "score": 4,
      "matched_cards": ["Consider", "Counterspell", ...]
    },
    ...
  }
  """
  results: dict[str, dict] = {}

  for archetype, signature_cards in archetype_signatures.items():
    matched_cards = sorted(deck_cards.intersection(signature_cards))
    results[archetype] = {
      "score": len(matched_cards),
      "matched_cards": matched_cards,
    }

  return results


def predict_archetype_from_scores(
  scores: dict[str, dict],
  rogue_threshold: int = DEFAULT_ROGUE_THRESHOLD,
) -> tuple[str, int]:
  if not scores:
    return "Rogue", 0

  best_archetype = max(
    scores,
    key=lambda archetype: (
      scores[archetype]["score"],
      archetype,
    ),
  )
  best_score = scores[best_archetype]["score"]

  if best_score < rogue_threshold:
    return "Rogue", best_score

  return best_archetype, best_score


def build_archetype_analysis_from_card_names(
  *,
  deck_id: int,
  deck_cards: set[str],
  rogue_threshold: int = DEFAULT_ROGUE_THRESHOLD,
  top_n: int = TOP_MATCHES_LIMIT,
) -> UserDeckArchetypeAnalysisResponse:
  if not deck_cards:
    raise HTTPException(status_code=422, detail="Deck has no cards to analyse")

  archetype_signatures = load_archetype_signatures()
  scores = score_deck_against_signatures(deck_cards, archetype_signatures)
  predicted_archetype, best_score = predict_archetype_from_scores(
    scores=scores,
    rogue_threshold=rogue_threshold,
  )

  sorted_matches = sorted(
    (
      ArchetypeMatchResponse(
        archetype=archetype,
        score=data["score"],
        matched_cards=data["matched_cards"],
      )
      for archetype, data in scores.items()
    ),
    key=lambda match: (-match.score, match.archetype),
  )[:top_n]

  return UserDeckArchetypeAnalysisResponse(
    deck_id=deck_id,
    predicted_archetype=predicted_archetype,
    best_score=best_score,
    rogue_threshold=rogue_threshold,
    card_count=len(deck_cards),
    top_matches=sorted_matches,
  )


def analyse_user_deck_archetype(
  deck_id: int,
  api_key: ApiKey,
  db: Session,
  rogue_threshold: int = DEFAULT_ROGUE_THRESHOLD,
) -> UserDeckArchetypeAnalysisResponse:
  deck = get_owned_deck_or_404(deck_id, api_key, db)
  deck_cards = extract_user_deck_card_names(deck)

  return build_archetype_analysis_from_card_names(
    deck_id=deck.id,
    deck_cards=deck_cards,
    rogue_threshold=rogue_threshold,
  )






class ClosestMetaDeckResponse(BaseModel):
  tournament_id: str
  deck_id: int
  spiciness: float
  win_percentage: float
  model_config = ConfigDict(from_attributes=True)


class UserDeckSpicinessAnalysisResponse(BaseModel):
  deck_id: int
  archetype: str
  start_date: datetime | None = None
  min_win_percentage: float | None = None
  compared_deck_count: int
  spiciness: float = Field(description="0 = identical to meta, 1 = nothing alike")
  closest_meta_decks: list[ClosestMetaDeckResponse]
  model_config = ConfigDict(from_attributes=True)


def _user_deck_to_vector(deck: UserDeck) -> dict[tuple[str, str], int]:
  vector: dict[tuple[str, str], int] = {}

  for card in deck.cards:
    card_name = _normalise_card_name(card.card_name)

    if (card.in_mainboard or 0) > 0:
      vector[(card_name, "main")] = int(card.in_mainboard)

    if (card.in_sideboard or 0) > 0:
      vector[(card_name, "side")] = int(card.in_sideboard)

  return vector


def _meta_deck_to_vector(deck_cards: list[DecklistCard]) -> dict[tuple[str, str], int]:
  vector: dict[tuple[str, str], int] = {}

  for card in deck_cards:
    card_name = _normalise_card_name(card.card_name)

    if (card.in_mainboard or 0) > 0:
      vector[(card_name, "main")] = int(card.in_mainboard)

    if (card.in_sideboard or 0) > 0:
      vector[(card_name, "side")] = int(card.in_sideboard)

  return vector


def _bray_curtis_spiciness(
  a: dict[tuple[str, str], int],
  b: dict[tuple[str, str], int],
) -> float:
  all_keys = set(a.keys()) | set(b.keys())
  if not all_keys:
    return 0.0

  numerator = sum(abs(a.get(key, 0) - b.get(key, 0)) for key in all_keys)
  denominator = sum(a.get(key, 0) + b.get(key, 0) for key in all_keys)

  if denominator == 0:
    return 0.0

  return round(numerator / denominator, 4)


def _deck_win_percentage(deck: Deck) -> float:
  wins = (deck.wins_swiss or 0) + (deck.bracket_wins or 0)
  losses = (deck.losses_swiss or 0) + (deck.bracket_losses or 0)
  draws = deck.draws or 0
  total_games = wins + losses + draws

  if total_games == 0:
    return 0.0

  return round((wins / total_games) * 100, 2)


def analyse_user_deck_spiciness(
  deck_id: int,
  archetype: str,
  start_date: datetime | None,
  min_win_percentage: float | None,
  api_key: ApiKey,
  db: Session,
) -> UserDeckSpicinessAnalysisResponse:
  user_deck = get_owned_deck_or_404(deck_id, api_key, db)
  user_vector = _user_deck_to_vector(user_deck)

  if not user_vector:
    raise HTTPException(status_code=422, detail="Deck has no cards to analyse")

  query = (
    db.query(Deck)
    .join(Tournament, Deck.tournament_id == Tournament.tid)
    .options(joinedload(Deck.decklist_cards))
    .filter(Deck.archetype == archetype.strip())
    .filter(Deck.decklist_processed.is_(True))
  )

  if start_date is not None:
    query = query.filter(Tournament.start_date >= int(start_date.timestamp()))

  meta_decks = query.all()

  comparisons: list[ClosestMetaDeckResponse] = []
  spicy_values: list[float] = []

  for meta_deck in meta_decks:
    win_pct = _deck_win_percentage(meta_deck)

    if min_win_percentage is not None and win_pct < min_win_percentage:
      continue

    meta_vector = _meta_deck_to_vector(meta_deck.decklist_cards)
    if not meta_vector:
      continue

    spicy = _bray_curtis_spiciness(user_vector, meta_vector)
    spicy_values.append(spicy)

    comparisons.append(
      ClosestMetaDeckResponse(
        tournament_id=meta_deck.tournament_id,
        deck_id=meta_deck.deck_id,
        spiciness=spicy,
        win_percentage=win_pct,
      )
    )

  if not spicy_values:
    raise HTTPException(
      status_code=404,
      detail="No meta decks matched the requested archetype and filters",
    )

  comparisons.sort(key=lambda d: (d.spiciness, -d.win_percentage, d.deck_id))

  return UserDeckSpicinessAnalysisResponse(
    deck_id=user_deck.id,
    archetype=archetype.strip(),
    start_date=start_date,
    min_win_percentage=min_win_percentage,
    compared_deck_count=len(spicy_values),
    spiciness=round(sum(spicy_values) / len(spicy_values), 4),
    closest_meta_decks=comparisons[:TOP_MATCHES_LIMIT],
  )