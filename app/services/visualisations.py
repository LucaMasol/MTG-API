import io
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.services.total_meta_analysis import get_meta_summary
from app.services.meta_analysis_over_time import get_meta_over_time_summary

def deck_count_chart(data):
  fig, ax = plt.subplots(figsize=(12, 6))
  ax.bar(data["archetypes"], data["deck_counts"])
  ax.set_title("Deck Count by Archetype")
  ax.set_ylabel("Deck Count")
  ax.tick_params(axis="x", rotation=90)

  buf = io.BytesIO()
  fig.tight_layout()
  fig.savefig(buf, format="png")
  plt.close(fig)
  buf.seek(0)

  return buf



def winrate_chart(data):
  fig, ax = plt.subplots(figsize=(12, 6))
  bars = ax.bar(data["archetypes"], data["winrates"], color=data["bar_colors"])

  ax.set_title("Winrate by Archetype")
  ax.set_ylabel("Winrate (%)")
  ax.tick_params(axis="x", rotation=90)
  ax.axhline(50, linestyle="--", color="red", label="50% baseline")

  for bar, winrate in zip(bars, data["winrates"]):
    ax.text(
      bar.get_x() + bar.get_width() / 2,
      bar.get_height(),
      f"{winrate:.1f}%",
      ha="center",
      va="bottom",
      fontsize=8
    )

  ax.legend()

  buf = io.BytesIO()
  fig.tight_layout()
  fig.savefig(buf, format="png")
  plt.close(fig)
  buf.seek(0)

  return buf



def meta_share_chart(data):
  fig, ax = plt.subplots(figsize=(8, 8))
  ax.pie(
    data["shares"],
    labels=data["archetypes"],
    autopct="%1.1f%%",
    startangle=90
  )

  ax.set_title("Metagame Share by Archetype")
  ax.axis("equal")

  buf = io.BytesIO()
  fig.tight_layout()
  fig.savefig(buf, format="png")
  plt.close(fig)
  buf.seek(0)

  return buf



def performance_scatter(data):
  fig, ax = plt.subplots(figsize=(10, 6))
  ax.scatter(data["shares"], data["winrates"])

  for x, y, label in zip(data["shares"], data["winrates"], data["labels"]):
    ax.text(x, y, label, fontsize=8)

  ax.set_title("Archetype Performance vs Meta Share")
  ax.set_xlabel("Meta Share (%)")
  ax.set_ylabel("Winrate (%)")
  ax.axhline(50, linestyle="--", color="red")

  buf = io.BytesIO()
  fig.tight_layout()
  fig.savefig(buf, format="png")
  plt.close(fig)
  buf.seek(0)

  return buf



def avg_wins_chart(data):
  fig, ax = plt.subplots(figsize=(12, 6))
  bars = ax.bar(data["archetypes"], data["avg_wins"])

  ax.set_title("Average Wins by Archetype")
  ax.set_ylabel("Average Wins")
  ax.tick_params(axis="x", rotation=90)

  for bar, val in zip(bars, data["avg_wins"]):
    ax.text(
      bar.get_x() + bar.get_width() / 2,
      bar.get_height(),
      f"{val:.2f}",
      ha="center",
      va="bottom",
      fontsize=8
    )

  buf = io.BytesIO()
  fig.tight_layout()
  fig.savefig(buf, format="png")
  plt.close(fig)
  buf.seek(0)

  return buf

def build_meta_share_stacked_area_chart(data):
    weeks = data["weeks"]
    archetypes = data["archetypes"]
    reversed_archetypes = list(reversed(archetypes))
    values = [data["series"][a] for a in reversed_archetypes]

    fig, ax = plt.subplots(figsize=(14, 8.2))
    ax.stackplot(weeks, values, labels=reversed_archetypes)

    ax.set_title("Metagame Share Over Time")
    ax.set_ylabel("Meta Share")
    ax.set_xlabel("Week")
    ax.set_ylim(0, 1)
    ax.tick_params(axis="x", rotation=90)

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
      handles[::-1],
      labels[::-1],
      loc="upper left",
      bbox_to_anchor=(1.02, 1)
    )

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)

    return buf


def build_winrate_over_time_chart(data):
  weeks = data["weeks"]

  fig, ax = plt.subplots(figsize=(14, 8.2))

  for archetype in data["archetypes"]:
    ax.plot(
      weeks,
      data["series"][archetype],
      marker="o",
      linewidth=1.8,
      label=archetype
    )

  ax.set_title("Winrate Over Time by Archetype")
  ax.set_xlabel("Week")
  ax.set_ylabel("Winrate (%)")
  ax.set_ylim(0, 100)
  ax.tick_params(axis="x", rotation=90)
  ax.axhline(50, linestyle="--", color="red", label="50% baseline")

  handles, labels = ax.get_legend_handles_labels()
  ax.legend(
    handles,
    labels,
    loc="upper left",
    bbox_to_anchor=(1.02, 1)
  )

  buf = io.BytesIO()
  fig.tight_layout()
  fig.savefig(buf, format="png")
  plt.close(fig)
  buf.seek(0)

  return buf



def build_avg_wins_over_time_chart(data):
  weeks = data["weeks"]

  fig, ax = plt.subplots(figsize=(14, 8.2))

  for archetype in data["archetypes"]:
    ax.plot(
      weeks,
      data["series"][archetype],
      marker="o",
      linewidth=1.8,
      label=archetype
    )

  ax.set_title("Average Wins Over Time by Archetype")
  ax.set_xlabel("Week")
  ax.set_ylabel("Average Wins")
  ax.tick_params(axis="x", rotation=90)

  handles, labels = ax.get_legend_handles_labels()
  ax.legend(
    handles,
    labels,
    loc="upper left",
    bbox_to_anchor=(1.02, 1)
  )

  buf = io.BytesIO()
  fig.tight_layout()
  fig.savefig(buf, format="png")
  plt.close(fig)
  buf.seek(0)

  return buf