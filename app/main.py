from fastapi import FastAPI, Query
from typing import List
from dotenv import load_dotenv
from datetime import datetime
from fastapi.responses import StreamingResponse
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
  build_avg_wins_over_time_chart
)
from app.services.meta_analysis_over_time import (
  get_meta_share_over_time_data,
  get_winrate_over_time_data,
  get_avg_wins_over_time_data
  )

load_dotenv()

app = FastAPI(
  title="MTG Meta Analytics API",
  description="API for analyzing Magic: The Gathering decks and metagame data",
  version="0.1"
)

@app.get("/")
def root():
  return {"message": "Server is running."}

@app.get("/meta")
def meta_overview():
  return get_meta_summary()



@app.get("/meta/deck-count")
def meta_deck_count_data(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  return get_deck_count_data(start_time, end_time)

@app.get("/meta/charts/deck-count.png")
def meta_chart_deck_count_png(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  buf = deck_count_chart(get_deck_count_data(start_time, end_time))
  return StreamingResponse(buf, media_type="image/png")



@app.get("/meta/winrate")
def meta_winrate_data(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  return get_winrate_data(start_time, end_time)

@app.get("/meta/charts/winrate.png")
def meta_chart_winrate_png(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  buf = winrate_chart(get_winrate_data(start_time, end_time))
  return StreamingResponse(buf, media_type="image/png")



@app.get("/meta/meta-share")
def meta_meta_share_data(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  return get_meta_share_data(start_time, end_time)

@app.get("/meta/charts/meta-share.png")
def meta_chart_meta_share_png(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  buf = meta_share_chart(get_meta_share_data(start_time, end_time))
  return StreamingResponse(buf, media_type="image/png")



@app.get("/meta/performance")
def meta_performance_data(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  return get_performance_scatter_data(start_time, end_time)

@app.get("/meta/charts/performance-scatter.png")
def meta_chart_performance_png(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  buf = performance_scatter(get_performance_scatter_data(start_time, end_time))
  return StreamingResponse(buf, media_type="image/png")



@app.get("/meta/avg-wins")
def meta_avg_wins_data(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  return get_avg_wins_data(start_time, end_time)

@app.get("/meta/charts/avg-wins.png")
def meta_chart_avg_wins_png(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
):
  buf = avg_wins_chart(get_avg_wins_data(start_time, end_time))
  return StreamingResponse(buf, media_type="image/png")



@app.get("/meta/over-time/meta-share")
def meta_share_over_time(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
  whitelist: List[str] | None = Query(default=None),
):
  return get_meta_share_over_time_data(
    start_time,
    end_time,
    whitelist
  )

@app.get("/meta/charts/over-time/meta-share.png")
def meta_share_over_time_chart(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
  whitelist: List[str] | None = Query(default=None),
):
  buf = build_meta_share_stacked_area_chart(get_meta_share_over_time_data(
    start_time,
    end_time,
    whitelist
  ))
  return StreamingResponse(buf, media_type="image/png")



@app.get("/meta/over-time/winrate")
def winrate_over_time(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
  whitelist: List[str] | None = Query(default=None),
):
  return get_winrate_over_time_data(
    start_time,
    end_time,
    whitelist
  )

@app.get("/meta/charts/over-time/winrate-line.png")
def winrate_over_time_chart(
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    whitelist: List[str] | None = Query(default=None),
):
  buf = build_winrate_over_time_chart(get_winrate_over_time_data(
    start_time,
    end_time,
    whitelist
  ))
  return StreamingResponse(buf, media_type="image/png")



@app.get("/meta/over-time/avg-wins")
def avg_wins_over_time(
  start_time: datetime | None = None,
  end_time: datetime | None = None,
  whitelist: List[str] | None = Query(default=None),
):
  return get_avg_wins_over_time_data(
    start_time,
    end_time,
    whitelist
  )

@app.get("/meta/charts/over-time/avg-wins.png")
def avg_wins_over_time_chart(
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    whitelist: List[str] | None = Query(default=None),
):
  buf = build_avg_wins_over_time_chart(get_avg_wins_over_time_data(
    start_time,
    end_time,
    whitelist
  ))
  return StreamingResponse(buf, media_type="image/png")