from sqlalchemy import func
from datetime import datetime
from app.database import SessionLocal
from app.models import Deck, Tournament


def get_meta_summary(
  start_time: datetime | None = None,
  end_time: datetime | None = None
):
  session = SessionLocal()

  try:
    query = (
      session.query(
        Deck.archetype,
        func.count().label("deck_count"),
        (func.sum(Deck.wins_swiss) + func.sum(Deck.bracket_wins)).label("wins"),
        (func.sum(Deck.losses_swiss) + func.sum(Deck.bracket_losses)).label("losses"),
        func.sum(Deck.draws).label("draws"),
        func.avg(Deck.wins_swiss).label("avg_wins"),
      )
      .join(Tournament, Deck.tournament_id == Tournament.tid)
      .filter(Deck.archetype.isnot(None))
    )

    if start_time is not None:
      query = query.filter(Tournament.start_date >= int(start_time.timestamp()))

    if end_time is not None:
      query = query.filter(Tournament.start_date <= int(end_time.timestamp()))

    total_decks = (
      session.query(func.count())
      .select_from(Deck)
      .join(Tournament, Deck.tournament_id == Tournament.tid)
      .filter(Deck.archetype.isnot(None))
    )

    if start_time is not None:
      total_decks = total_decks.filter(Tournament.start_date >= int(start_time.timestamp()))

    if end_time is not None:
      total_decks = total_decks.filter(Tournament.start_date <= int(end_time.timestamp()))

    total_decks = total_decks.scalar() or 0

    results = (
      query.group_by(Deck.archetype)
      .order_by(func.count().desc())
      .all()
    )

    meta = []

    for row in results:
      total_games = (row.wins or 0) + (row.losses or 0) + (row.draws or 0)
      winrate = (row.wins / total_games) if total_games else 0

      meta.append({
        "archetype": row.archetype,
        "deck_count": row.deck_count,
        "meta_share": (row.deck_count / total_decks) if total_decks else 0,
        "wins": int(row.wins or 0),
        "losses": int(row.losses or 0),
        "draws": int(row.draws or 0),
        "winrate": round(winrate, 3),
        "avg_wins": float(row.avg_wins or 0),
      })

    return meta

  finally:
    session.close()



def get_deck_count_data(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  meta = sorted(get_meta_summary(start_time, end_time), key=lambda x: x["deck_count"], reverse=True)

  return {
    "archetypes": [row["archetype"] for row in meta],
    "deck_counts": [row["deck_count"] for row in meta]
  }
  
  

def get_winrate_data(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  meta = sorted(get_meta_summary(start_time, end_time), key=lambda x: x["winrate"], reverse=True)

  archetypes = [row["archetype"] for row in meta]
  winrates = [row["winrate"] * 100 for row in meta]
  bar_colors = [
    "green" if winrate > 50 else "blue" if winrate == 50 else "red"
    for winrate in winrates
  ]

  return {
    "archetypes": archetypes,
    "winrates": winrates,
    "bar_colors": bar_colors
  }



def get_meta_share_data(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  meta = sorted(get_meta_summary(start_time, end_time), key=lambda x: x["meta_share"], reverse=True)

  return {
    "archetypes": [row["archetype"] for row in meta],
    "shares": [row["meta_share"] for row in meta]
  }
  
  
  
def get_performance_scatter_data(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  meta = get_meta_summary(start_time, end_time)

  return {
    "shares": [row["meta_share"] * 100 for row in meta],
    "winrates": [row["winrate"] * 100 for row in meta],
    "labels": [row["archetype"] for row in meta]
  }



def get_avg_wins_data(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  meta = sorted(get_meta_summary(start_time, end_time), key=lambda x: x["avg_wins"], reverse=True)

  return {
    "archetypes": [row["archetype"] for row in meta],
    "avg_wins": [row["avg_wins"] for row in meta]
  }