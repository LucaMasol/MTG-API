from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.services.authentication_and_security import get_api_key_record
from app.services.database_helpers import get_db
from app.services.user_decks import (
  CreateUserDeckRequest,
  RenameUserDeckRequest,
  DeckCardsUpsertRequest,
  UserDeckResponse,
  UserDeckListResponse,
  UserDeckListItem,
  UserDeckDetailResponse,
  create_user_deck,
  list_user_decks,
  get_user_deck,
  rename_user_deck,
  replace_user_deck_cards,
  append_user_deck_cards,
  delete_card_from_user_deck,
  delete_user_deck,
  serialize_user_deck,
)

router = APIRouter(
  prefix="/user-decks",
  tags=["user-decks"],
  dependencies=[Depends(get_api_key_record)],
)


@router.post(
  "",
  response_model=UserDeckResponse,
  status_code=status.HTTP_201_CREATED,
  summary="Create a new user deck",
)
def create_user_deck_route(
  payload: CreateUserDeckRequest,
  db: Session = Depends(get_db),
):
  return create_user_deck(payload, api_key, db)


@router.get(
  "",
  response_model=UserDeckListResponse,
  summary="List all decks for the authenticated user",
)
def list_user_decks_route(
  db: Session = Depends(get_db),
):
  decks = list_user_decks(api_key, db)
  return UserDeckListResponse(
    decks=[UserDeckListItem(id=deck.id, name=deck.name) for deck in decks]
  )


@router.get(
  "/{deck_id}",
  response_model=UserDeckDetailResponse,
  summary="Get a single user deck",
)
def get_user_deck_route(
  deck_id: int,
  db: Session = Depends(get_db),
):
  deck = get_user_deck(deck_id, api_key, db)
  return serialize_user_deck(deck)


@router.put(
  "/{deck_id}",
  response_model=UserDeckResponse,
  summary="Rename a user deck",
)
def rename_user_deck_route(
  deck_id: int,
  payload: RenameUserDeckRequest,
  db: Session = Depends(get_db),
):
  return rename_user_deck(deck_id, payload, api_key, db)


@router.post(
  "/{deck_id}/cards",
  response_model=UserDeckDetailResponse,
  summary="Replace all cards in a user deck",
)
def replace_user_deck_cards_route(
  deck_id: int,
  payload: DeckCardsUpsertRequest,
  db: Session = Depends(get_db),
):
  deck = replace_user_deck_cards(deck_id, payload, api_key, db)
  return serialize_user_deck(deck)


@router.put(
  "/{deck_id}/cards",
  response_model=UserDeckDetailResponse,
  summary="Append/update cards in a user deck",
)
def append_user_deck_cards_route(
  deck_id: int,
  payload: DeckCardsUpsertRequest,
  db: Session = Depends(get_db),
):
  deck = append_user_deck_cards(deck_id, payload, api_key, db)
  return serialize_user_deck(deck)


@router.delete(
  "/{deck_id}/cards/{card_name}",
  status_code=status.HTTP_204_NO_CONTENT,
  summary="Delete a card from a user deck",
)
def delete_card_from_user_deck_route(
  deck_id: int,
  card_name: str,
  db: Session = Depends(get_db),
):
  delete_card_from_user_deck(deck_id, card_name, api_key, db)
  return None


@router.delete(
  "/{deck_id}",
  status_code=status.HTTP_204_NO_CONTENT,
  summary="Delete a user deck",
)
def delete_user_deck_route(
  deck_id: int,
  db: Session = Depends(get_db),
):
  delete_user_deck(deck_id, api_key, db)
  return None