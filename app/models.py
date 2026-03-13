from sqlalchemy import (
  Column,
  Boolean,
  Integer,
  String,
  BigInteger,
  ForeignKey,
  ForeignKeyConstraint,
  DateTime
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

# Tournament table
# Used for data relating to tournaments
class Tournament(Base):
  __tablename__ = "tournaments"

  tid = Column(String, primary_key=True)
  tournament_name = Column(String, nullable=False)
  format = Column(String, nullable=False)
  players = Column(Integer, nullable=False)
  start_date = Column(BigInteger, nullable=False)
  swiss_rounds = Column(Integer, nullable=False)

  decks = relationship(
    "Deck",
    back_populates="tournament",
    cascade="all, delete-orphan"
)

# Deck table
# Used for information on a deck, like how it did, along with the link to the decklist
class Deck(Base):
  __tablename__ = "decks"

  tournament_id = Column(
    String,
    ForeignKey("tournaments.tid", ondelete="CASCADE"),
    primary_key=True
  )
  deck_id = Column(Integer, primary_key=True)

  name = Column(String, nullable=True)
  moxfield_decklist = Column(String, nullable=True)
  wins_swiss = Column(Integer, nullable=False, default=0)
  losses_swiss = Column(Integer, nullable=False, default=0)
  draws = Column(Integer, nullable=False, default=0)
  bracket_wins = Column(Integer, nullable=False, default=0)
  bracket_losses = Column(Integer, nullable=False, default=0)
  decklist_processed = Column(Boolean, nullable=False, default=False)
  archetype = Column(String, nullable=True)

  tournament = relationship("Tournament", back_populates="decks")
  decklist_cards = relationship(
    "DecklistCard",
    back_populates="deck",
    cascade="all, delete-orphan"
  )


# Card table
# Every card used in the decks in the database
class Card(Base):
  __tablename__ = "cards"

  card_name = Column(String, primary_key=True)

  decklist_entries = relationship("DecklistCard", back_populates="card")
  user_deck_entries = relationship("UserDecklistCard", back_populates="card")


# Decklist table
# For each deck in each tournament, lists each card in the decklist
class DecklistCard(Base):
  __tablename__ = "decklist_cards"

  tournament_id = Column(String, primary_key=True)
  deck_id = Column(Integer, primary_key=True)
  card_name = Column(
    String,
    ForeignKey("cards.card_name", ondelete="CASCADE"),
    primary_key=True
  )

  in_mainboard = Column(Integer, nullable=False, default=0)
  in_sideboard = Column(Integer, nullable=False, default=0)

  __table_args__ = (
    ForeignKeyConstraint(
      ["tournament_id", "deck_id"],
      ["decks.tournament_id", "decks.deck_id"],
      ondelete="CASCADE",
    ),
  )

  deck = relationship("Deck", back_populates="decklist_cards")
  card = relationship("Card", back_populates="decklist_entries")


class User(Base):
  __tablename__ = "users"

  id = Column(Integer, primary_key=True, index=True)
  email = Column(String, unique=True, nullable=False, index=True)
  password_hash = Column(String, nullable=False)
  is_active = Column(Boolean, default=True, nullable=False)
  created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

  api_keys = relationship("ApiKey", back_populates="user")
  decks = relationship("UserDeck", back_populates="user", cascade="all, delete-orphan")


class ApiKey(Base):
  __tablename__ = "api_keys"

  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

  key_prefix = Column(String, nullable=False, index=True)
  key_hash = Column(String, unique=True, nullable=False, index=True)

  is_blocked = Column(Boolean, default=False, nullable=False)
  blocked_until = Column(DateTime, nullable=True)

  request_count = Column(Integer, default=0, nullable=False)
  window_started_at = Column(DateTime, default=datetime.utcnow, nullable=False)

  created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

  user = relationship("User", back_populates="api_keys")


class UserDeck(Base):
  __tablename__ = "user_decks"

  id = Column(Integer, primary_key=True, index=True)
  user_email = Column(
    String,
    ForeignKey("users.email", ondelete="CASCADE"),
    nullable=False,
    index=True,
  )
  name = Column(String, nullable=False)

  user = relationship(
    "User",
    back_populates="decks",
    foreign_keys=[user_email],
    primaryjoin="User.email == UserDeck.user_email",
  )

  cards = relationship(
    "UserDecklistCard",
    back_populates="deck",
    cascade="all, delete-orphan"
  )


class UserDecklistCard(Base):
  __tablename__ = "user_decklist_cards"

  deck_id = Column(
    Integer,
    ForeignKey("user_decks.id", ondelete="CASCADE"),
    primary_key=True
  )
  card_name = Column(
    String,
    ForeignKey("cards.card_name", ondelete="CASCADE"),
    primary_key=True
  )

  in_mainboard = Column(Integer, nullable=False, default=0)
  in_sideboard = Column(Integer, nullable=False, default=0)

  deck = relationship("UserDeck", back_populates="cards")
  card = relationship("Card", back_populates="user_deck_entries")