"""Backend API contract tests for the Birthlight Human Design service.

Covers:
- Health/root
- City catalog (list, search, id lookup, not-found)
- Blueprint creation (happy path + validation errors)
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import requests


def _load_backend_url() -> str:
    """Prefer EXPO_PUBLIC_BACKEND_URL from frontend/.env (platform standard)."""
    for key in ("EXPO_PUBLIC_BACKEND_URL", "EXPO_BACKEND_URL"):
        v = os.environ.get(key)
        if v:
            return v.rstrip("/")

    env_path = Path(__file__).resolve().parents[2] / "frontend" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    raise RuntimeError("EXPO_PUBLIC_BACKEND_URL not set")


BASE_URL = _load_backend_url()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_root_ok():
    r = requests.get(f"{BASE_URL}/api/", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, dict)
    assert "message" in body


# ---------------------------------------------------------------------------
# Cities: default catalog
# ---------------------------------------------------------------------------

CITY_FIELDS = {
    "id", "name", "country", "country_code",
    "latitude", "longitude", "timezone", "population",
}


def test_cities_default_list():
    r = requests.get(f"{BASE_URL}/api/cities", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 20, f"expected ~20+ default cities, got {len(data)}"
    for city in data:
        assert CITY_FIELDS.issubset(city.keys()), city.keys()
        assert isinstance(city["latitude"], float)
        assert isinstance(city["longitude"], float)
        assert isinstance(city["population"], int)


def test_cities_search_bandung():
    r = requests.get(f"{BASE_URL}/api/cities", params={"q": "Bandung", "limit": 5}, timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Must include Indonesian Bandung id=1650357, tz=Asia/Jakarta.
    hit = next((c for c in data if c["id"] == "1650357"), None)
    assert hit is not None, f"Bandung id=1650357 missing from results: {[c['id'] for c in data]}"
    assert hit["timezone"] == "Asia/Jakarta"
    assert hit["country_code"] == "ID"


def test_cities_search_london():
    r = requests.get(f"{BASE_URL}/api/cities", params={"q": "London"}, timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert any(c["name"].lower() == "london" and c["country_code"] == "GB" for c in data), \
        f"London, UK missing from results: {[(c['name'], c['country_code']) for c in data[:5]]}"


def test_city_by_id_bandung():
    r = requests.get(f"{BASE_URL}/api/cities/1650357", timeout=15)
    assert r.status_code == 200
    city = r.json()
    assert city["id"] == "1650357"
    assert city["name"] == "Bandung"
    assert city["timezone"] == "Asia/Jakarta"
    assert city["country_code"] == "ID"


def test_city_by_id_not_found():
    r = requests.get(f"{BASE_URL}/api/cities/does-not-exist", timeout=15)
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Blueprint: happy path
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def yosep_blueprint():
    payload = {
        "name": "Yosep",
        "birth_date": "09-12-1976",
        "birth_time": "15:37",
        "city_id": "1650357",
    }
    r = requests.post(f"{BASE_URL}/api/blueprint", json=payload, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


def test_blueprint_shape(yosep_blueprint):
    expected_keys = {
        "id", "name", "city", "birth_date", "birth_time",
        "type", "strategy", "authority", "profile",
        "defined_centers", "defined_channels", "active_gates",
        "personality", "design",
    }
    assert expected_keys.issubset(yosep_blueprint.keys()), (
        expected_keys - set(yosep_blueprint.keys())
    )
    assert yosep_blueprint["name"] == "Yosep"
    assert yosep_blueprint["birth_date"] == "09-12-1976"
    assert yosep_blueprint["birth_time"] == "15:37"
    city = yosep_blueprint["city"]
    assert city["id"] == "1650357"
    assert city["timezone"] == "Asia/Jakarta"


def test_blueprint_type_authority_profile(yosep_blueprint):
    # Reference values currently computed by the engine.
    assert yosep_blueprint["type"] == "Generator", yosep_blueprint["type"]
    assert yosep_blueprint["authority"] == "Sacral", yosep_blueprint["authority"]
    assert yosep_blueprint["profile"] == "1/3", yosep_blueprint["profile"]
    assert yosep_blueprint["strategy"] == "Wait to Respond", yosep_blueprint["strategy"]


def test_blueprint_activations(yosep_blueprint):
    for key in ("personality", "design"):
        acts = yosep_blueprint[key]
        assert isinstance(acts, list)
        assert len(acts) == 13, f"{key} has {len(acts)} activations"
        for a in acts:
            assert 1 <= a["gate"] <= 64, a
            assert 1 <= a["line"] <= 6, a
            assert 0.0 <= float(a["longitude"]) < 360.0
            assert isinstance(a["label"], str) and a["label"]


# ---------------------------------------------------------------------------
# Blueprint: validation errors
# ---------------------------------------------------------------------------

def _post_blueprint(**overrides):
    payload = {
        "name": "Yosep",
        "birth_date": "09-12-1976",
        "birth_time": "15:37",
        "city_id": "1650357",
    }
    payload.update(overrides)
    return requests.post(f"{BASE_URL}/api/blueprint", json=payload, timeout=30)


def test_blueprint_rejects_iso_date():
    r = _post_blueprint(birth_date="1976-12-09")
    assert r.status_code == 400, r.text


def test_blueprint_rejects_impossible_date():
    r = _post_blueprint(birth_date="31-02-1990")
    assert r.status_code == 400, r.text


def test_blueprint_rejects_empty_name():
    r = _post_blueprint(name="")
    # Pydantic may still accept empty then service returns 400; or Pydantic 422.
    # Contract says "must return 400".
    assert r.status_code == 400, f"expected 400, got {r.status_code}: {r.text}"


def test_blueprint_rejects_invalid_city():
    r = _post_blueprint(city_id="does-not-exist")
    assert r.status_code == 400, r.text
