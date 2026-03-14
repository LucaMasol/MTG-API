import requests
import random
import pytest
import json
from pathlib import Path
import time
import os

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_PREFIX = "/api/v1"


def new_test_user(email=None):
  data = {
    "email": email or f"testing{random.randint(0, 99999)}@email.com",
    "password": "securepassword"
  }

  r = requests.post(f"{BASE_URL}{API_PREFIX}/auth/signup", json=data)

  body = {}
  try:
    body = r.json()
  except Exception:
    pass

  return {"email":data["email"], "api_key":body.get("api_key"), "status_code":r.status_code}

@pytest.fixture
def test_user():
  # BEFORE EACH TEST
  user = new_test_user()

  yield user

  # AFTER EACH TEST
  pass

@pytest.fixture
def test_user_w_deck():
  # BEFORE EACH TEST
  user = new_test_user()

  headers = {"X-API-Key": user["api_key"]}
  data = {
    "name": "Test Deck",
  }

  user['deck'] = requests.post(f"{BASE_URL}{API_PREFIX}/user-decks", json=data, headers=headers).json()["id"]

  yield user

  # AFTER EACH TEST
  pass


@pytest.fixture
def small_decklist_data():
  with Path("data/small_decklist.json").open("r", encoding="utf-8") as f:
    return json.load(f)

@pytest.fixture
def normal_decklist_data():
  with Path("data/example_elves_decklist.json").open("r", encoding="utf-8") as f:
    return json.load(f)

@pytest.fixture
def combined_decklist_data():
  with Path("data/combined_decklist.json").open("r", encoding="utf-8") as f:
    return json.load(f)


def test_server_running():
  """Check the API is reachable"""
  r = requests.get(f"{BASE_URL}/docs")
  if r.status_code != 200:
    pytest.exit(f"Stopping test run: server check failed (status {r.status_code})", returncode=1)


def test_signup_new_user():
  """Test creating a new user"""
  data = {
    "email": f"testing{random.randint(0, 99999)}@email.com",
    "password": "securepassword"
  }

  r = requests.post(f"{BASE_URL}{API_PREFIX}/auth/signup", json=data)

  if r.status_code != 201:
    pytest.exit(f"Stopping test run: signup pre-check failed (status {r.status_code})", returncode=1)


def test_signup_existing_user(test_user):
  """Test attempting to create a new user"""
  existing_user_response = new_test_user(email=test_user["email"])

  assert existing_user_response["status_code"] == 409


def test_get_user_decks(test_user):
  """Check authenticated endpoint"""
  headers = {"X-API-Key": test_user["api_key"]}

  r = requests.get(f"{BASE_URL}{API_PREFIX}/user-decks", headers=headers)

  assert r.status_code == 200
  assert isinstance(r.json()["decks"], list)


def test_create_deck(test_user):
  """Create a new deck"""
  headers = {"X-API-Key": test_user["api_key"]}

  data = {
    "name": "Test Deck",
  }

  r = requests.post(f"{BASE_URL}{API_PREFIX}/user-decks", json=data, headers=headers)

  assert r.status_code == 201


def test_meta_endpoint(test_user):
  """Test analytics/meta endpoint"""
  headers = {"X-API-Key": test_user["api_key"]}
  r = requests.get(f"{BASE_URL}{API_PREFIX}/meta/summary", headers=headers)

  assert r.status_code == 200
  assert isinstance(r.json()[0], dict)


def test_post_decklist(test_user_w_deck, small_decklist_data, normal_decklist_data):
  """POST data twice to a decklist"""
  headers = {"X-API-Key": test_user_w_deck["api_key"]}
  post_r1 = requests.post(
    f"{BASE_URL}{API_PREFIX}/user-decks/{test_user_w_deck['deck']}/cards",
    json=normal_decklist_data,
    headers=headers
  )
  post_r2 = requests.post(
    f"{BASE_URL}{API_PREFIX}/user-decks/{test_user_w_deck['deck']}/cards",
    json=small_decklist_data,
    headers=headers
  )
  get_r = requests.get(
    f"{BASE_URL}{API_PREFIX}/user-decks/{test_user_w_deck['deck']}/cards",
    headers=headers
  )

  assert post_r1.status_code == 201
  assert post_r2.status_code == 201
  assert get_r.status_code == 200
  assert isinstance(get_r.json(), dict)
  assert get_r.json() == small_decklist_data


def test_put_decklist(test_user_w_deck, small_decklist_data, normal_decklist_data, combined_decklist_data):
  """PUT data in a decklist"""
  headers = {"X-API-Key": test_user_w_deck["api_key"]}
  post_r = requests.post(
    f"{BASE_URL}{API_PREFIX}/user-decks/{test_user_w_deck['deck']}/cards",
    json=normal_decklist_data,
    headers=headers
  )
  put_r = requests.put(
    f"{BASE_URL}{API_PREFIX}/user-decks/{test_user_w_deck['deck']}/cards",
    json=small_decklist_data,
    headers=headers
  )
  get_r = requests.get(
    f"{BASE_URL}{API_PREFIX}/user-decks/{test_user_w_deck['deck']}/cards",
    headers=headers
  )

  assert post_r.status_code == 201
  assert put_r.status_code == 200
  assert get_r.status_code == 200
  assert isinstance(get_r.json(), dict)
  assert get_r.json() == combined_decklist_data


def test_delete_from_decklist(test_user_w_deck, normal_decklist_data):
  """DELETE data in a decklist"""
  headers = {"X-API-Key": test_user_w_deck["api_key"]}
  requests.post(
    f"{BASE_URL}{API_PREFIX}/user-decks/{test_user_w_deck['deck']}/cards",
    json=normal_decklist_data,
    headers=headers
  )

  requests.put(
    f"{BASE_URL}{API_PREFIX}/user-decks/{test_user_w_deck['deck']}/cards",
    json={
      "cards": {
        "Plains": { "mainboard": 3,   "sideboard": 0 }
      }
    },
    headers=headers
  )

  delete_r = requests.delete(
    f"{BASE_URL}{API_PREFIX}/user-decks/{test_user_w_deck['deck']}/cards/Plains",
    headers=headers
  )

  get_r = requests.get(
    f"{BASE_URL}{API_PREFIX}/user-decks/{test_user_w_deck['deck']}/cards",
    headers=headers
  )


  assert delete_r.status_code == 204
  assert isinstance(get_r.json(), dict)
  assert get_r.json() == normal_decklist_data



def test_estimate_archetype(test_user_w_deck, normal_decklist_data):
  """Estimate archetype for user deck"""
  headers = {"X-API-Key": test_user_w_deck["api_key"]}
  requests.post(
    f"{BASE_URL}{API_PREFIX}/user-decks/{test_user_w_deck['deck']}/cards",
    json=normal_decklist_data,
    headers=headers
  )

  r = requests.get(
    f"{BASE_URL}{API_PREFIX}/user-decks/{test_user_w_deck['deck']}/analysis/archetype",
    headers=headers
  )

  assert r.status_code == 200
  assert r.json()["predicted_archetype"] == "Elves"