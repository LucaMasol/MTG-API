from collections import defaultdict
from datetime import datetime

from sqlalchemy import func
from app.database import SessionLocal
from app.models import Deck, Tournament


def _unix_timestamp(dt: datetime | None) -> int | None:
  if dt is None:
    return None
  return int(dt.timestamp())

# Returns weekly grouped archetype statistics
def get_meta_over_time_summary(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
  whitelist: list[str] | None = None,
):
  session = SessionLocal()

  try:
    week_bucket = func.date_trunc(
      "week",
      func.to_timestamp(Tournament.start_date)
    )

    query = (
      session.query(
        week_bucket.label("week"),
        Deck.archetype.label("archetype"),
        func.count().label("deck_count"),
        (func.sum(Deck.wins_swiss) + func.sum(Deck.bracket_wins)).label("wins"),
        (func.sum(Deck.losses_swiss) + func.sum(Deck.bracket_losses)).label("losses"),
        func.sum(Deck.draws).label("draws"),
        func.avg(Deck.wins_swiss).label("avg_wins"),
      )
      .join(Tournament, Deck.tournament_id == Tournament.tid)
      .filter(Deck.archetype.isnot(None))
    )

    start_unix = _unix_timestamp(start_time)
    end_unix = _unix_timestamp(end_time)

    # Bound data to start date
    if start_unix is not None:
      query = query.filter(Tournament.start_date >= start_unix)

    # Bound data to end date
    if end_unix is not None:
      query = query.filter(Tournament.start_date <= end_unix)

    # If specified, limit returned data to the whitelist
    if whitelist:
      query = query.filter(Deck.archetype.in_(whitelist))

    results = (
      query.group_by(week_bucket, Deck.archetype)
      .order_by(week_bucket.asc(), Deck.archetype.asc())
      .all()
    )

    summary = []

    for row in results:
      summary.append({
        "week": row.week.strftime("%Y-%m-%d"),
        "archetype": row.archetype,
        "deck_count": row.deck_count,
        "wins": int(row.wins or 0),
        "losses": int(row.losses or 0),
        "draws": int(row.draws or 0),
        "avg_wins": float(row.avg_wins or 0),
      })

    return summary

  finally:
    session.close()



def get_meta_share_over_time_data(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
  whitelist: list[str] | None = None,
):
    summary = get_meta_over_time_summary(start_time, end_time, whitelist)

    grouped = defaultdict(dict)
    all_archetypes = set()

    for row in summary:
      grouped[row["week"]][row["archetype"]] = row["deck_count"]
      all_archetypes.add(row["archetype"])

    weeks = sorted(grouped.keys())
    archetypes = sorted(all_archetypes)

    series = {archetype: [] for archetype in archetypes}

    for week in weeks:
      total_decks = sum(grouped[week].values())

      for archetype in archetypes:
        count = grouped[week].get(archetype, 0)
        share = (count / total_decks) if total_decks else 0
        series[archetype].append(round(share, 4))

    return {
      "weeks": weeks,
      "archetypes": archetypes,
      "series": series,
    }



def get_winrate_over_time_data(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
  whitelist: list[str] | None = None,
):
    summary = get_meta_over_time_summary(start_time, end_time, whitelist)

    grouped = defaultdict(dict)
    all_archetypes = set()

    for row in summary:
        total_games = row["wins"] + row["losses"] + row["draws"]
        winrate = (row["wins"] / total_games) if total_games else 0

        grouped[row["week"]][row["archetype"]] = round(winrate * 100, 2)
        all_archetypes.add(row["archetype"])

    weeks = sorted(grouped.keys())
    archetypes = sorted(all_archetypes)

    series = {archetype: [] for archetype in archetypes}

    for week in weeks:
        for archetype in archetypes:
            series[archetype].append(grouped[week].get(archetype))

    return {
        "weeks": weeks,
        "archetypes": archetypes,
        "series": series,
    }



def get_avg_wins_over_time_data(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
  whitelist: list[str] | None = None,
):
  summary = get_meta_over_time_summary(start_time, end_time, whitelist)

  grouped = defaultdict(dict)
  all_archetypes = set()

  for row in summary:
    grouped[row["week"]][row["archetype"]] = round(row["avg_wins"], 2)
    all_archetypes.add(row["archetype"])

  weeks = sorted(grouped.keys())
  archetypes = sorted(all_archetypes)

  series = {archetype: [] for archetype in archetypes}

  for week in weeks:
    for archetype in archetypes:
        series[archetype].append(grouped[week].get(archetype))

  return {
    "weeks": weeks,
    "archetypes": archetypes,
    "series": series,
  }