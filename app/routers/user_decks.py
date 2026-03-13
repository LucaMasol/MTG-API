from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

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
  serialise_user_deck,
)
from app.services.deck_analysis import (
  UserDeckArchetypeAnalysisResponse,
  analyse_user_deck_archetype,
  UserDeckSpicinessAnalysisResponse,
  analyse_user_deck_spiciness,
)

router = APIRouter(
  prefix="/user-decks",
  tags=["user-decks"],
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
  api_key=Depends(get_api_key_record),
):
  return create_user_deck(payload, api_key, db)


@router.get(
  "",
  response_model=UserDeckListResponse,
  summary="List all decks for the authenticated user",
)
def list_user_decks_route(
  db: Session = Depends(get_db),
  api_key=Depends(get_api_key_record),
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
  api_key=Depends(get_api_key_record),
):
  deck = get_user_deck(deck_id, api_key, db)
  return serialise_user_deck(deck)


@router.put(
  "/{deck_id}",
  response_model=UserDeckResponse,
  summary="Rename a user deck",
)
def rename_user_deck_route(
  deck_id: int,
  payload: RenameUserDeckRequest,
  db: Session = Depends(get_db),
  api_key=Depends(get_api_key_record),
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
  api_key=Depends(get_api_key_record),
):
  deck = replace_user_deck_cards(deck_id, payload, api_key, db)
  return serialise_user_deck(deck)


@router.put(
  "/{deck_id}/cards",
  response_model=UserDeckDetailResponse,
  summary="Append/update cards in a user deck",
)
def append_user_deck_cards_route(
  deck_id: int,
  payload: DeckCardsUpsertRequest,
  db: Session = Depends(get_db),
  api_key=Depends(get_api_key_record),
):
  deck = append_user_deck_cards(deck_id, payload, api_key, db)
  return serialise_user_deck(deck)


@router.delete(
  "/{deck_id}/cards/{card_name:path}",
  status_code=status.HTTP_204_NO_CONTENT,
  summary="Delete a card from a user deck",
)
def delete_card_from_user_deck_route(
  deck_id: int,
  card_name: str,
  db: Session = Depends(get_db),
  api_key=Depends(get_api_key_record),
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
  api_key=Depends(get_api_key_record),
):
  delete_user_deck(deck_id, api_key, db)
  return None


@router.get(
  "/{deck_id}/analysis/archetype",
  response_model=UserDeckArchetypeAnalysisResponse,
  summary="Estimate the archetype of a user deck",
)
def analyse_user_deck_archetype_route(
  deck_id: int,
  rogue_threshold: int = Query(
    default=3,
    ge=1,
    le=20,
    description="Compares decklist with core cards from archetypes to classify the decks",
  ),
  db: Session = Depends(get_db),
  api_key=Depends(get_api_key_record),
):
  return analyse_user_deck_archetype(
    deck_id=deck_id,
    api_key=api_key,
    db=db,
    rogue_threshold=rogue_threshold,
  )



@router.get(
  "/{deck_id}/analysis/spiciness",
  response_model=UserDeckSpicinessAnalysisResponse,
  summary="Measure how unusual a user deck is versus a chosen archetype in the meta",
)
def analyse_user_deck_spiciness_route(
  deck_id: int,
  archetype: str = Query(..., min_length=1, description="Archetype to compare against"),
  start_date: datetime | None = Query(
    default=None,
    description="Only include meta decks from this date onward",
  ),
  win_percentage: float | None = Query(
    default=None,
    ge=0,
    le=100,
    description="Minimum win percentage required for meta decks to be included",
  ),
  db: Session = Depends(get_db),
  api_key=Depends(get_api_key_record),
):
  return analyse_user_deck_spiciness(
    deck_id=deck_id,
    archetype=archetype,
    start_date=start_date,
    min_win_percentage=win_percentage,
    api_key=api_key,
    db=db,
  )