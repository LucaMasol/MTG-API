from datetime import datetime
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.services.authentication_and_security import get_api_key_record
from app.services.database_helpers import get_db
from app.services.user_decks import (
  CreateUserDeckRequest,
  RenameUserDeckRequest,
  DeckCardsUpsertRequest,
  CardQuantityUpdate,
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

COMMON_USER_DECK_RESPONSES = {
  401: {
    "description": "Missing or invalid API key",
    "content": {
      "application/json": {
        "example": {"detail": "Missing API key"}
      }
    },
  },
  404: {
    "description": "Requested deck was not found for the authenticated user",
    "content": {
      "application/json": {
        "example": {"detail": "Deck not found"}
      }
    },
  },
  422: {
    "description": "Validation error",
  },
}


@router.post(
  "",
  response_model=UserDeckResponse,
  status_code=status.HTTP_201_CREATED,
  summary="Create a new user deck",
  description="Creates an empty deck owned by the authenticated user.",
  responses={
    **COMMON_USER_DECK_RESPONSES,
    201: {
      "description": "Deck created successfully",
      "content": {
        "application/json": {
          "example": {
            "id": 1,
            "user_email": "test@example.com",
            "name": "Elves Testing List"
          }
        }
      },
    },
  },
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
  description="Returns all decks owned by the authenticated user.",
  responses={
    **COMMON_USER_DECK_RESPONSES,
    200: {
      "content": {
        "application/json": {
          "example": {
            "decks": [
              {"id": 1, "name": "Elves Testing List"},
              {"id": 2, "name": "Mono Blue Brew"}
            ]
          }
        }
      }
    },
  },
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
  description="Returns a single user deck, including its cards and quantities.",
  responses={
    **COMMON_USER_DECK_RESPONSES,
    200: {
      "content": {
        "application/json": {
          "example": {
            "id": 1,
            "user_email": "test@example.com",
            "name": "Elves Testing List",
            "cards": [
              {"card_name": "Llanowar Elves", "mainboard": 4, "sideboard": 0},
              {"card_name": "Hydroblast", "mainboard": 0, "sideboard": 3}
            ]
          }
        }
      }
    },
  },
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
  description="Updates the name of a deck owned by the authenticated user.",
  responses={
    **COMMON_USER_DECK_RESPONSES,
    200: {
      "content": {
        "application/json": {
          "example": {
            "id": 1,
            "user_email": "test@example.com",
            "name": "Updated Deck Name"
          }
        }
      }
    },
  },
)
def rename_user_deck_route(
  deck_id: int,
  payload: RenameUserDeckRequest,
  db: Session = Depends(get_db),
  api_key=Depends(get_api_key_record),
):
  return rename_user_deck(deck_id, payload, api_key, db)


@router.get(
  "/{deck_id}/cards",
  response_model=DeckCardsUpsertRequest,
  summary="Get cards from a user deck",
  description="Returns the deck's cards as a card-name keyed map of mainboard and sideboard quantities.",
  responses={
    **COMMON_USER_DECK_RESPONSES,
    200: {
      "content": {
        "application/json": {
          "example": {
            "cards": {
              "Llanowar Elves": {"mainboard": 4, "sideboard": 0},
              "Hydroblast": {"mainboard": 0, "sideboard": 3}
            }
          }
        }
      }
    },
  },
)
def get_user_deck_cards_route(
  deck_id: int,
  db: Session = Depends(get_db),
  api_key=Depends(get_api_key_record),
):
  deck = get_user_deck(deck_id, api_key, db)
  return DeckCardsUpsertRequest(
    cards={
      card.card_name: CardQuantityUpdate(
        mainboard=card.in_mainboard,
        sideboard=card.in_sideboard,
      )
      for card in sorted(deck.cards, key=lambda c: c.card_name.lower())
    }
  )


@router.post(
  "/{deck_id}/cards",
  response_model=UserDeckDetailResponse,
  summary="Replace all cards in a user deck",
  description=(
    "Replaces the entire decklist with the submitted card map. "
    "Any existing cards in the deck are removed before the new list is inserted."
  ),
  responses={
    **COMMON_USER_DECK_RESPONSES,
    200: {
      "description": "Decklist replaced successfully",
      "content": {
        "application/json": {
          "example": {
            "id": 1,
            "user_email": "test@example.com",
            "name": "Elves Testing List",
            "cards": {
              "Llanowar Elves": {"mainboard": 4, "sideboard": 0},
              "Priest of Titania": {"mainboard": 4, "sideboard": 0},
              "Hydroblast": {"mainboard": 0, "sideboard": 3}
            }
          }
        }
      }
    },
  },
)
def replace_user_deck_cards_route(
  deck_id: int,
  payload: DeckCardsUpsertRequest,
  db: Session = Depends(get_db),
  api_key=Depends(get_api_key_record),
):
  """
  Example request body:

  {
    "cards": {
      "Llanowar Elves": {"mainboard": 4, "sideboard": 0},
      "Priest of Titania": {"mainboard": 4, "sideboard": 0},
      "Hydroblast": {"mainboard": 0, "sideboard": 3}
    }
  }
  """
  deck = replace_user_deck_cards(deck_id, payload, api_key, db)
  return serialise_user_deck(deck)


@router.put(
  "/{deck_id}/cards",
  response_model=UserDeckDetailResponse,
  summary="Append or update cards in a user deck",
  description=(
    "Adds cards that are not yet present in the deck and updates quantities for cards that already exist. "
    "Unlike POST on this route, this does not clear the existing decklist first."
  ),
  responses={
    **COMMON_USER_DECK_RESPONSES,
    200: {
      "description": "Decklist updated successfully",
      "content": {
        "application/json": {
          "example": {
            "id": 1,
            "user_email": "test@example.com",
            "name": "Elves Testing List",
            "cards": [
              {"card_name": "Llanowar Elves", "mainboard": 4, "sideboard": 0},
              {"card_name": "Hydroblast", "mainboard": 0, "sideboard": 4}
            ]
          }
        }
      }
    },
  },
)
def append_user_deck_cards_route(
  deck_id: int,
  payload: DeckCardsUpsertRequest,
  db: Session = Depends(get_db),
  api_key=Depends(get_api_key_record),
):
  """
  Example request body:

  {
    "cards": {
      "Hydroblast": {"mainboard": 0, "sideboard": 1},
      "Blue Elemental Blast": {"mainboard": 0, "sideboard": 2}
    }
  }
  """
  deck = append_user_deck_cards(deck_id, payload, api_key, db)
  return serialise_user_deck(deck)


@router.delete(
  "/{deck_id}/cards/{card_name:path}",
  status_code=status.HTTP_204_NO_CONTENT,
  summary="Delete a card from a user deck",
  description=(
    "Deletes a single card entry from the specified user deck. "
    "The card name is part of the URL path, so names containing spaces or special characters "
    "should be URL-encoded by the client."
  ),
  responses=COMMON_USER_DECK_RESPONSES,
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
  description="Deletes a deck owned by the authenticated user.",
  responses=COMMON_USER_DECK_RESPONSES,
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
  description=(
    "Classifies the user deck by comparing its card names against stored archetype signature cards. "
    "If the best score is below the rogue_threshold, the deck is labeled as Rogue."
  ),
  responses={
    **COMMON_USER_DECK_RESPONSES,
    200: {
      "content": {
        "application/json": {
          "example": {
            "deck_id": 1,
            "predicted_archetype": "Elves",
            "best_score": 6,
            "rogue_threshold": 3,
            "card_count": 18,
            "top_matches": [
              {
                "archetype": "Elves",
                "score": 6,
                "matched_cards": [
                  "Birchlore Rangers",
                  "Llanowar Elves",
                  "Priest of Titania"
                ]
              }
            ]
          }
        }
      }
    },
  },
)
def analyse_user_deck_archetype_route(
  deck_id: int,
  rogue_threshold: int = Query(
    default=3,
    ge=1,
    le=20,
    description=(
      "Minimum top archetype signature match score required to avoid classifying "
      "the deck as Rogue. Lower values make archetype matching easier."
    ),
    examples=[3],
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
  description=(
    "Compares the selected user deck against meta decks from a chosen archetype and "
    "returns a spiciness score, where 0 means very similar to the meta and 1 means very different."
  ),
  responses={
    **COMMON_USER_DECK_RESPONSES,
    200: {
      "content": {
        "application/json": {
          "example": {
            "deck_id": 1,
            "archetype": "Elves",
            "start_date": "2025-01-01T00:00:00",
            "min_win_percentage": 50.0,
            "compared_deck_count": 18,
            "spiciness": 0.27,
            "closest_meta_decks": [
              {
                "tournament_id": "123456",
                "deck_id": 2,
                "spiciness": 0.18,
                "win_percentage": 66.7
              }
            ]
          }
        }
      }
    },
  },
)
def analyse_user_deck_spiciness_route(
  deck_id: int,
  archetype: str = Query(
    ...,
    min_length=1,
    description="Archetype name to compare against, for example 'Elves' or 'Mono Blue Terror'.",
    examples=["Elves"],
  ),
  start_date: datetime | None = Query(
    default=None,
    description="Only include meta decks from this datetime onward.",
    examples=["2025-01-01T00:00:00"],
  ),
  win_percentage: float | None = Query(
    default=None,
    ge=0,
    le=100,
    description="Minimum win percentage required for meta decks to be included in the comparison set.",
    examples=[50],
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