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


@router.get("/summary")
def meta_summary(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  return get_meta_summary(start_time, end_time)


@router.get("/deck-count")
def meta_deck_count(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  return get_deck_count_data(start_time, end_time)


@router.get("/charts/deck-count.png")
def meta_chart_deck_count(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  buf = deck_count_chart(get_deck_count_data(start_time, end_time))
  return StreamingResponse(buf, media_type="image/png")


@router.get("/winrate")
def meta_winrate(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  return get_winrate_data(start_time, end_time)


@router.get("/charts/winrate.png")
def meta_chart_winrate(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  buf = winrate_chart(get_winrate_data(start_time, end_time))
  return StreamingResponse(buf, media_type="image/png")


@router.get("/meta-share")
def meta_share(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  return get_meta_share_data(start_time, end_time)


@router.get("/charts/meta-share.png")
def meta_chart_meta_share(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  buf = meta_share_chart(get_meta_share_data(start_time, end_time))
  return StreamingResponse(buf, media_type="image/png")


@router.get("/performance")
def meta_performance(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  return get_performance_scatter_data(start_time, end_time)


@router.get("/charts/performance-scatter.png")
def meta_chart_performance(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  buf = performance_scatter(get_performance_scatter_data(start_time, end_time))
  return StreamingResponse(buf, media_type="image/png")


@router.get("/avg-wins")
def meta_avg_wins(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  return get_avg_wins_data(start_time, end_time)


@router.get("/charts/avg-wins.png")
def meta_chart_avg_wins(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  buf = avg_wins_chart(get_avg_wins_data(start_time, end_time))
  return StreamingResponse(buf, media_type="image/png")


@router.get("/meta-share-over-time")
def meta_share_over_time(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
  whitelist: List[str] | None = Query(default=None),
):
  return get_meta_share_over_time_data(start_time, end_time, whitelist)


@router.get("/charts/meta-share-over-time.png")
def meta_share_over_time_chart(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
  whitelist: List[str] | None = Query(default=None),
):
  buf = build_meta_share_stacked_area_chart(
    get_meta_share_over_time_data(start_time, end_time, whitelist)
  )
  return StreamingResponse(buf, media_type="image/png")


@router.get("/winrate-over-time")
def winrate_over_time(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
  whitelist: List[str] | None = Query(default=None),
):
  return get_winrate_over_time_data(start_time, end_time, whitelist)


@router.get("/charts/winrate-over-time.png")
def winrate_over_time_chart(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
  whitelist: List[str] | None = Query(default=None),
):
  buf = build_winrate_over_time_chart(
    get_winrate_over_time_data(start_time, end_time, whitelist)
  )
  return StreamingResponse(buf, media_type="image/png")


@router.get("/avg-wins-over-time")
def avg_wins_over_time(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
  whitelist: List[str] | None = Query(default=None),
):
  return get_avg_wins_over_time_data(start_time, end_time, whitelist)


@router.get("/charts/avg-wins-over-time.png")
def avg_wins_over_time_chart(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
  whitelist: List[str] | None = Query(default=None),
):
  buf = build_avg_wins_over_time_chart(
    get_avg_wins_over_time_data(start_time, end_time, whitelist)
  )
  return StreamingResponse(buf, media_type="image/png")


@router.get("/decks/{deck_id}")
def get_meta_deck(
   deck_id: int,
   tournament_id: int = Query(..., description="Tournament ID for the deck"),
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