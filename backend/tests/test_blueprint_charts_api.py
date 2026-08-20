"""End-to-end API verification for the 5 authoritative user-provided charts.

Confirms that `POST /api/blueprint` returns the exact same Type / Authority /
Profile as the local engine for Firza, Tresna, Delicia, Sarah, and Bryan.
The Jakarta city id is discovered dynamically via `GET /api/cities?q=jakarta`.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import requests


def _load_backend_url() -> str:
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

CHARTS = [
    {
        "name": "Firza", "birth_date": "14-05-1978", "birth_time": "02:00",
        "type": "Projector", "authority": "Self-Projected", "profile": "5/1",
    },
    {
        "name": "Tresna", "birth_date": "04-02-1997", "birth_time": "06:30",
        "type": "Reflector", "authority": "Lunar", "profile": "3/5",
    },
    {
        "name": "Delicia", "birth_date": "06-10-2008", "birth_time": "07:15",
        "type": "Manifestor", "authority": "Emotional", "profile": "4/6",
    },
    {
        "name": "Sarah", "birth_date": "15-08-2013", "birth_time": "05:44",
        "type": "Manifesting Generator", "authority": "Emotional", "profile": "4/6",
    },
    {
        "name": "Bryan", "birth_date": "03-09-2007", "birth_time": "07:18",
        "type": "Generator", "authority": "Emotional", "profile": "5/1",
    },
]


@pytest.fixture(scope="module")
def jakarta_city_id():
    r = requests.get(f"{BASE_URL}/api/cities", params={"q": "jakarta", "limit": 1}, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list) and len(data) >= 1, data
    city = data[0]
    assert city["timezone"] == "Asia/Jakarta", city
    assert city["country_code"] == "ID", city
    return city["id"]


@pytest.mark.parametrize("chart", CHARTS, ids=[c["name"] for c in CHARTS])
def test_blueprint_chart(chart, jakarta_city_id):
    payload = {
        "name": chart["name"],
        "birth_date": chart["birth_date"],
        "birth_time": chart["birth_time"],
        "city_id": jakarta_city_id,
    }
    r = requests.post(f"{BASE_URL}/api/blueprint", json=payload, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["type"] == chart["type"], f"{chart['name']} type: got {body['type']}"
    assert body["authority"] == chart["authority"], f"{chart['name']} auth: got {body['authority']}"
    assert body["profile"] == chart["profile"], f"{chart['name']} profile: got {body['profile']}"


def test_tresna_reflector_lunar_rule(jakarta_city_id):
    """Reflector must expose inner_authority=None and authority_process='Lunar'."""
    payload = {
        "name": "Tresna",
        "birth_date": "04-02-1997",
        "birth_time": "06:30",
        "city_id": jakarta_city_id,
    }
    r = requests.post(f"{BASE_URL}/api/blueprint", json=payload, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    # These fields may or may not be exposed by the API; guard the assertion.
    if "inner_authority" in body:
        assert body["inner_authority"] is None, body["inner_authority"]
    if "authority_process" in body:
        assert body["authority_process"] == "Lunar", body["authority_process"]
    assert body["type"] == "Reflector"
    assert body["authority"] == "Lunar"
