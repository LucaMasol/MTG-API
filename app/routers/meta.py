from datetime import datetime
from typing import List

from sqlalchemy.orm import Session, joinedload
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse

from app.services.database_helpers import get_db
from app.models import Deck
from app.services.authentication_and_security import get_api_key_record
from app.services.total_meta_analysis import (
  get_meta_summary,
  get_deck_count_data,
  get_winrate_data,
  get_meta_share_data,
  get_performance_scatter_data,
  get_avg_wins_data,
)
from app.services.visualisations import (
  deck_count_chart,
  winrate_chart,
  meta_share_chart,
  performance_scatter,
  avg_wins_chart,
  build_meta_share_stacked_area_chart,
  build_winrate_over_time_chart,
  build_avg_wins_over_time_chart,
)
from app.services.meta_analysis_over_time import (
  get_meta_share_over_time_data,
  get_winrate_over_time_data,
  get_avg_wins_over_time_data,
)

router = APIRouter(
  prefix="/meta",
  tags=["meta"],
  dependencies=[Depends(get_api_key_record)]
)

COMMON_META_RESPONSES = {
  200: {"description": "Successful response"},
  401: {
    "description": "Missing or invalid API key",
    "content": {
      "application/json": {
        "example": {"detail": "Missing API key"}
      }
    },
  },
  429: {
    "description": "API key temporarily rate-limited",
    "content": {
      "application/json": {
        "example": {"detail": "Rate limit exceeded. API key blocked for 5 minutes."}
      }
    },
  },
}

DATE_PARAM_START = Query(
  default=None,
  description="Lower datetime bound for tournament data filtering.",
  examples=["2025-01-01T00:00:00"],
)

DATE_PARAM_END = Query(
  default=None,
  description="Upper datetime bound for tournament data filtering.",
  examples=["2025-03-01T23:59:59"],
)

WHITELIST_PARAM = Query(
  default=None,
  description=(
    "Optional list of archetype names to include."
    "Repeat the parameter to pass multiple values."
  ),
  examples=["Mono Blue Terror", "Elves"],
)

TOURNAMENT_ID_PARAM = Query(
  ...,
  description="Tournament identifier for the requested deck.",
  examples=["123456"],
)


@router.get(
  "/summary",
  summary="Get overall metagame summary",
  description=(
    "Returns aggregate metagame statistics grouped by archetype"
  ),
  responses={
    **COMMON_META_RESPONSES,
    200: {
      "description": "Metagame summary returned successfully",
      "content": {
        "application/json": {
          "example": [
            {
              "archetype": "Mono Blue Terror",
              "deck_count": 42,
              "meta_share": 0.184,
              "wins": 110,
              "losses": 80,
              "draws": 6,
              "winrate": 0.561,
              "avg_wins": 2.62
            }
          ]
        }
      },
    },
  },
)
def meta_summary(
  start_time: datetime | None = DATE_PARAM_START,
  end_time: datetime | None = DATE_PARAM_END,
):
  return get_meta_summary(start_time, end_time)


@router.get(
  "/deck-count",
  summary="Get deck counts by archetype",
  description="Returns archetype names and total deck counts for selected date range.",
  responses={
    **COMMON_META_RESPONSES,
    200: {
      "content": {
        "application/json": {
          "example": {
            "archetypes": ["Mono Blue Terror", "Elves", "Grixis Affinity"],
            "deck_counts": [42, 35, 28]
          }
        }
      }
    },
  },
)
def meta_deck_count(
  start_time: datetime | None = DATE_PARAM_START,
  end_time: datetime | None = DATE_PARAM_END,
):
  return get_deck_count_data(start_time, end_time)


@router.get(
  "/charts/deck-count.png",
  summary="Get deck count chart",
  description="Returns a PNG bar chart showing deck counts by archetype.",
  responses=COMMON_META_RESPONSES,
)
def meta_chart_deck_count(
  start_time: datetime | None = DATE_PARAM_START,
  end_time: datetime | None = DATE_PARAM_END,
):
  buf = deck_count_chart(get_deck_count_data(start_time, end_time))
  return StreamingResponse(buf, media_type="image/png")


@router.get(
  "/winrate",
  summary="Get winrate by archetype",
  description="Returns archetypes ordered by winrate across selected date range.",
  responses={
    **COMMON_META_RESPONSES,
    200: {
      "content": {
        "application/json": {
          "example": {
            "archetypes": ["Mono Blue Terror", "Elves"],
            "winrates": [56.1, 53.4],
            "bar_colors": ["green", "green"]
          }
        }
      }
    },
  },
)
def meta_winrate(
  start_time: datetime | None = DATE_PARAM_START,
  end_time: datetime | None = DATE_PARAM_END,
):
  return get_winrate_data(start_time, end_time)


@router.get(
  "/charts/winrate.png",
  summary="Get winrate chart",
  description="Returns a PNG bar chart showing archetype winrates.",
  responses=COMMON_META_RESPONSES,
)
def meta_chart_winrate(
  start_time: datetime | None = DATE_PARAM_START,
  end_time: datetime | None = DATE_PARAM_END,
):
  buf = winrate_chart(get_winrate_data(start_time, end_time))
  return StreamingResponse(buf, media_type="image/png")


@router.get(
  "/meta-share",
  summary="Get metagame share by archetype",
  description="Returns archetypes and their share of the metagame for selected date range.",
  responses={
    **COMMON_META_RESPONSES,
    200: {
      "content": {
        "application/json": {
          "example": {
            "archetypes": ["Mono Blue Terror", "Elves"],
            "shares": [18.4, 15.3]
          }
        }
      }
    },
  },
)
def meta_share(
  start_time: datetime | None = DATE_PARAM_START,
  end_time: datetime | None = DATE_PARAM_END,
):
  return get_meta_share_data(start_time, end_time)


@router.get(
  "/charts/meta-share.png",
  summary="Get metagame share chart",
  description="Returns a PNG pie chart showing metagame share by archetype.",
  responses=COMMON_META_RESPONSES,
)
def meta_chart_meta_share(
  start_time: datetime | None = DATE_PARAM_START,
  end_time: datetime | None = DATE_PARAM_END,
):
  buf = meta_share_chart(get_meta_share_data(start_time, end_time))
  return StreamingResponse(buf, media_type="image/png")


@router.get(
  "/performance",
  summary="Get archetype performance scatter data",
  description=(
    "Returns data for plotting archetype meta share against winrate."
  ),
  responses={
    **COMMON_META_RESPONSES,
    200: {
      "content": {
        "application/json": {
          "example": {
            "labels": ["Mono Blue Terror", "Elves"],
            "shares": [18.4, 15.3],
            "winrates": [56.1, 53.4]
          }
        }
      }
    },
  },
)
def meta_performance(
  start_time: datetime | None = DATE_PARAM_START,
  end_time: datetime | None = DATE_PARAM_END,
):
  return get_performance_scatter_data(start_time, end_time)


@router.get(
  "/charts/performance-scatter.png",
  summary="Get archetype performance scatter chart",
  description="Returns a PNG scatter chart of meta share against winrate.",
  responses=COMMON_META_RESPONSES,
)
def meta_chart_performance(
  start_time: datetime | None = DATE_PARAM_START,
  end_time: datetime | None = DATE_PARAM_END,
):
  buf = performance_scatter(get_performance_scatter_data(start_time, end_time))
  return StreamingResponse(buf, media_type="image/png")


@router.get(
  "/avg-wins",
  summary="Get average wins by archetype",
  description="Returns archetypes and their average swiss wins for selected date range.",
  responses={
    **COMMON_META_RESPONSES,
    200: {
      "content": {
        "application/json": {
          "example": {
            "archetypes": ["Mono Blue Terror", "Elves"],
            "avg_wins": [2.62, 2.41]
          }
        }
      }
    },
  },
)
def meta_avg_wins(
  start_time: datetime | None = DATE_PARAM_START,
  end_time: datetime | None = DATE_PARAM_END,
):
  return get_avg_wins_data(start_time, end_time)


@router.get(
  "/charts/avg-wins.png",
  summary="Get average wins chart",
  description="Returns a PNG bar chart showing average wins by archetype.",
  responses=COMMON_META_RESPONSES,
)
def meta_chart_avg_wins(
  start_time: datetime | None = DATE_PARAM_START,
  end_time: datetime | None = DATE_PARAM_END,
):
  buf = avg_wins_chart(get_avg_wins_data(start_time, end_time))
  return StreamingResponse(buf, media_type="image/png")


@router.get(
  "/meta-share-over-time",
  summary="Get metagame share over time",
  description=(
    "Returns weekly metagame share time-series data."
    "Use the whitelist parameter to restrict results to specific archetypes."
  ),
  responses={
    **COMMON_META_RESPONSES,
    200: {
      "content": {
        "application/json": {
          "example": {
            "weeks": ["2025-01-06", "2025-01-13"],
            "archetypes": ["Mono Blue Terror", "Elves"],
            "series": {
              "Mono Blue Terror": [0.18, 0.21],
              "Elves": [0.14, 0.12]
            }
          }
        }
      }
    },
  },
)
def meta_share_over_time(
  start_time: datetime | None = DATE_PARAM_START,
  end_time: datetime | None = DATE_PARAM_END,
  whitelist: List[str] | None = WHITELIST_PARAM,
):
  return get_meta_share_over_time_data(start_time, end_time, whitelist)


@router.get(
  "/charts/meta-share-over-time.png",
  summary="Get metagame share over time chart",
  description="Returns a PNG stacked area chart of metagame share over time.",
  responses=COMMON_META_RESPONSES,
)
def meta_share_over_time_chart(
  start_time: datetime | None = DATE_PARAM_START,
  end_time: datetime | None = DATE_PARAM_END,
  whitelist: List[str] | None = WHITELIST_PARAM,
):
  buf = build_meta_share_stacked_area_chart(
    get_meta_share_over_time_data(start_time, end_time, whitelist)
  )
  return StreamingResponse(buf, media_type="image/png")


@router.get(
  "/winrate-over-time",
  summary="Get winrate over time",
  description="Returns weekly winrate time-series data for archetypes.",
  responses={
    **COMMON_META_RESPONSES,
    200: {
      "content": {
        "application/json": {
          "example": {
            "weeks": ["2025-01-06", "2025-01-13"],
            "archetypes": ["Mono Blue Terror", "Elves"],
            "series": {
              "Mono Blue Terror": [55.2, 57.8],
              "Elves": [51.0, 49.5]
            }
          }
        }
      }
    },
  },
)
def winrate_over_time(
  start_time: datetime | None = DATE_PARAM_START,
  end_time: datetime | None = DATE_PARAM_END,
  whitelist: List[str] | None = WHITELIST_PARAM,
):
  return get_winrate_over_time_data(start_time, end_time, whitelist)


@router.get(
  "/charts/winrate-over-time.png",
  summary="Get winrate over time chart",
  description="Returns a PNG line chart of archetype winrate over time.",
  responses=COMMON_META_RESPONSES,
)
def winrate_over_time_chart(
  start_time: datetime | None = DATE_PARAM_START,
  end_time: datetime | None = DATE_PARAM_END,
  whitelist: List[str] | None = WHITELIST_PARAM,
):
  buf = build_winrate_over_time_chart(
    get_winrate_over_time_data(start_time, end_time, whitelist)
  )
  return StreamingResponse(buf, media_type="image/png")


@router.get(
  "/avg-wins-over-time",
  summary="Get average wins over time",
  description="Returns weekly average wins time-series data for archetypes.",
  responses={
    **COMMON_META_RESPONSES,
    200: {
      "content": {
        "application/json": {
          "example": {
            "weeks": ["2025-01-06", "2025-01-13"],
            "archetypes": ["Mono Blue Terror", "Elves"],
            "series": {
              "Mono Blue Terror": [2.6, 2.8],
              "Elves": [2.2, 2.1]
            }
          }
        }
      }
    },
  },
)
def avg_wins_over_time(
  start_time: datetime | None = DATE_PARAM_START,
  end_time: datetime | None = DATE_PARAM_END,
  whitelist: List[str] | None = WHITELIST_PARAM,
):
  return get_avg_wins_over_time_data(start_time, end_time, whitelist)


@router.get(
  "/charts/avg-wins-over-time.png",
  summary="Get average wins over time chart",
  description="Returns a PNG line chart of average wins over time.",
  responses=COMMON_META_RESPONSES,
)
def avg_wins_over_time_chart(
  start_time: datetime | None = DATE_PARAM_START,
  end_time: datetime | None = DATE_PARAM_END,
  whitelist: List[str] | None = WHITELIST_PARAM,
):
  buf = build_avg_wins_over_time_chart(
    get_avg_wins_over_time_data(start_time, end_time, whitelist)
  )
  return StreamingResponse(buf, media_type="image/png")


@router.get(
  "/decks/{deck_id}",
  summary="Get a specific meta deck and its decklist",
  description=(
    "Returns a single tournament deck entry, including archetype, tournament id, "
    "and sorted mainboard and sideboard card lists. "
    "Because deck_id is only unique within a tournament, tournament_id is also required."
  ),
  responses={
    **COMMON_META_RESPONSES,
    200: {
      "content": {
        "application/json": {
          "example": {
            "deck_id": 1,
            "deck_name": "Mono Blue Terror",
            "archetype": "Mono Blue Terror",
            "tournament_id": "123456",
            "mainboard": [
              {"card_name": "Consider", "quantity": 4},
              {"card_name": "Counterspell", "quantity": 4}
            ],
            "sideboard": [
              {"card_name": "Blue Elemental Blast", "quantity": 3}
            ]
          }
        }
      }
    },
    404: {
      "description": "Deck not found",
      "content": {
        "application/json": {
          "example": {"detail": "Deck not found"}
        }
      },
    },
  },
)
def get_meta_deck(
  deck_id: int,
  tournament_id: str = TOURNAMENT_ID_PARAM,
  db: Session = Depends(get_db),
):
  deck = (
    db.query(Deck)
    .options(joinedload(Deck.decklist_cards))
    .filter(
      Deck.deck_id == deck_id,
      Deck.tournament_id == tournament_id,
    )
    .first()
  )

  if deck is None:
    raise HTTPException(status_code=404, detail="Deck not found")

  mainboard = []
  sideboard = []

  for card in deck.decklist_cards:
    if (card.in_mainboard or 0) > 0:
      mainboard.append({
        "card_name": card.card_name,
        "quantity": card.in_mainboard
      })

    if (card.in_sideboard or 0) > 0:
      sideboard.append({
        "card_name": card.card_name,
        "quantity": card.in_sideboard
      })

  return {
    "deck_id": deck.deck_id,
    "deck_name": deck.name,
    "archetype": deck.archetype,
    "tournament_id": deck.tournament_id,
    "mainboard": sorted(mainboard, key=lambda x: x["card_name"]),
    "sideboard": sorted(sideboard, key=lambda x: x["card_name"]),
  }