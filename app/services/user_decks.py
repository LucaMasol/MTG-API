from typing import Dict, Annotated
from fastapi import HTTPException
from pydantic import BaseModel, StringConstraints, ConfigDict
from sqlalchemy.orm import Session

from app.models import Card, ApiKey, UserDeck, UserDecklistCard

NameStr = Annotated[
  str,
  StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
]

class CreateUserDeckRequest(BaseModel):
  name: NameStr


class RenameUserDeckRequest(BaseModel):
  name: NameStr


class UserDeckResponse(BaseModel):
  id: int
  user_email: str
  name: str
  model_config = ConfigDict(from_attributes=True)


class UserDeckListItem(BaseModel):
  id: int
  name: str
  model_config = ConfigDict(from_attributes=True)


class UserDeckListResponse(BaseModel):
  decks: list[UserDeckListItem]


class CardQuantityUpdate(BaseModel):
  mainboard: int = 0
  sideboard: int = 0


class DeckCardsUpsertRequest(BaseModel):
  cards: Dict[str, CardQuantityUpdate]


class DeckCardResponse(BaseModel):
  card_name: str
  mainboard: int
  sideboard: int


class UserDeckDetailResponse(BaseModel):
  id: int
  user_email: str
  name: str
  cards: list[DeckCardResponse]
  model_config = ConfigDict(from_attributes=True)

# Make sure the deck exists and belongs to the authenticated user
def _get_owned_deck_or_404(deck_id: int, api_key: ApiKey, db: Session) -> UserDeck:
  deck = (
    db.query(UserDeck)
    .filter(
      UserDeck.id == deck_id,
      UserDeck.user_email == api_key.user.email,
    )
    .first()
  )
  if not deck:
    raise HTTPException(status_code=404, detail="Deck not found")
  return deck


# If card does not exist in the shared card table, add it
def _ensure_card_exists(card_name: str, db: Session) -> Card:
  normalised_name = card_name.strip()
  if not normalised_name:
    raise HTTPException(status_code=422, detail="Card name cannot be empty")
  card = db.query(Card).filter(Card.card_name == normalised_name).first()
  if not card:
    card = Card(card_name=normalised_name)
    db.add(card)
    db.flush()
  return card


def create_user_deck(payload: CreateUserDeckRequest, api_key: ApiKey, db: Session) -> UserDeck:
  deck = UserDeck(
    user_email=api_key.user.email,
    name=payload.name,
  )
  db.add(deck)
  db.commit()
  db.refresh(deck)
  return deck


def list_user_decks(api_key: ApiKey, db: Session) -> list[UserDeck]:
  return (
    db.query(UserDeck)
    .filter(UserDeck.user_email == api_key.user.email)
    .order_by(UserDeck.id.asc())
    .all()
  )


def get_user_deck(deck_id: int, api_key: ApiKey, db: Session) -> UserDeck:
  return _get_owned_deck_or_404(deck_id, api_key, db)


def rename_user_deck(
  deck_id: int,
  payload: RenameUserDeckRequest,
  api_key: ApiKey,
  db: Session,
) -> UserDeck:
  deck = _get_owned_deck_or_404(deck_id, api_key, db)
  deck.name = payload.name
  db.commit()
  db.refresh(deck)
  return deck


# For use with the POST request, as it first deletes all cards in the deck
def replace_user_deck_cards(
  deck_id: int,
  payload: DeckCardsUpsertRequest,
  api_key: ApiKey,
  db: Session,
) -> UserDeck:
  deck = _get_owned_deck_or_404(deck_id, api_key, db)

  db.query(UserDecklistCard).filter(UserDecklistCard.deck_id == deck.id).delete()

  for card_name, qty in payload.cards.items():
    card = _ensure_card_exists(card_name, db)

    mainboard = max(0, qty.mainboard)
    sideboard = max(0, qty.sideboard)

    if mainboard == 0 and sideboard == 0:
      continue

    entry = UserDecklistCard(
      deck_id=deck.id,
      card_name=card.card_name,
      in_mainboard=mainboard,
      in_sideboard=sideboard,
    )
    db.add(entry)

  db.commit()
  db.refresh(deck)
  return deck


# PUT behaviour: increment/decrement card quantities without clearing deck
def append_user_deck_cards(
  deck_id: int,
  payload: DeckCardsUpsertRequest,
  api_key: ApiKey,
  db: Session,
) -> UserDeck:
  deck = _get_owned_deck_or_404(deck_id, api_key, db)

  for card_name, qty in payload.cards.items():
    normalised_card = _ensure_card_exists(card_name, db)

    entry = (
      db.query(UserDecklistCard)
      .filter(
        UserDecklistCard.deck_id == deck.id,
        UserDecklistCard.card_name == normalised_card.card_name,
      )
      .first()
    )

    if not entry:
      new_main = max(0, qty.mainboard)
      new_side = max(0, qty.sideboard)

      if new_main == 0 and new_side == 0:
        continue

      entry = UserDecklistCard(
        deck_id=deck.id,
        card_name=normalised_card.card_name,
        in_mainboard=new_main,
        in_sideboard=new_side,
      )
      db.add(entry)
    else:
      entry.in_mainboard = max(0, entry.in_mainboard + qty.mainboard)
      entry.in_sideboard = max(0, entry.in_sideboard + qty.sideboard)

      if entry.in_mainboard == 0 and entry.in_sideboard == 0:
        db.delete(entry)

  db.commit()
  db.refresh(deck)
  return deck


def delete_card_from_user_deck(
  deck_id: int,
  card_name: str,
  api_key: ApiKey,
  db: Session,
) -> None:
  deck = _get_owned_deck_or_404(deck_id, api_key, db)
  normalised_card_name = card_name.strip()

  entry = (
    db.query(UserDecklistCard)
    .filter(
      UserDecklistCard.deck_id == deck.id,
      UserDecklistCard.card_name == normalised_card_name,
    )
    .first()
  )

  if not entry:
    raise HTTPException(status_code=404, detail="Card not found in deck")

  db.delete(entry)
  db.commit()


def delete_user_deck(deck_id: int, api_key: ApiKey, db: Session) -> None:
  deck = _get_owned_deck_or_404(deck_id, api_key, db)
  db.delete(deck)
  db.commit()


# Convert deck and cards into the API response schema
def serialise_user_deck(deck: UserDeck) -> UserDeckDetailResponse:
  cards = sorted(deck.cards, key=lambda c: c.card_name.lower())
  return UserDeckDetailResponse(
    id=deck.id,
    user_email=deck.user_email,
    name=deck.name,
    cards=[
      DeckCardResponse(
        card_name=card.card_name,
        mainboard=card.in_mainboard,
        sideboard=card.in_sideboard,
      )
      for card in cards
    ],
  )