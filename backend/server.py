from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from human_design import calculate_human_design

import geonamescache
from timezonefinder import TimezoneFinder


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection (kept for platform compatibility; not used for persistence).
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ---------------------------------------------------------------------------
# City catalog (global, powered by geonamescache + timezonefinder)
# ---------------------------------------------------------------------------

_gc = geonamescache.GeonamesCache()
_tf = TimezoneFinder()
_countries = _gc.get_countries()  # {'ID': {'name': 'Indonesia', ...}, ...}
_raw_cities = list(_gc.get_cities().values())  # ~24k cities >= 15k population

# A curated seed of default cities shown when no query is provided.
_DEFAULT_CITY_KEYS = [
    "Jakarta", "Bandung", "Surabaya", "Yogyakarta", "Denpasar", "Medan", "Makassar",
    "Singapore", "Kuala Lumpur", "Bangkok", "Manila", "Tokyo", "Seoul", "Hong Kong",
    "Sydney", "London", "Paris", "New York City", "Los Angeles", "Berlin",
    "Dubai", "Mumbai", "Beijing", "Shanghai", "Toronto", "Sao Paulo",
]


def _tz_for(lat: float, lon: float) -> str:
    tz = _tf.timezone_at(lat=lat, lng=lon)
    if tz is None:
        tz = _tf.closest_timezone_at(lat=lat, lng=lon) or "UTC"
    return tz


def _city_to_dict(city: Dict[str, Any]) -> Dict[str, Any]:
    lat = float(city["latitude"])
    lon = float(city["longitude"])
    country_code = city.get("countrycode", "")
    country_name = _countries.get(country_code, {}).get("name", country_code)
    return {
        "id": str(city["geonameid"]),
        "name": city["name"],
        "country": country_name,
        "country_code": country_code,
        "latitude": lat,
        "longitude": lon,
        "timezone": _tz_for(lat, lon),
        "population": int(city.get("population", 0)),
    }


# Precompute default cities (largest match by name in seed list) so the initial
# picker request is instant.
_default_cities_cache: List[Dict[str, Any]] = []
_seen_ids = set()
for key in _DEFAULT_CITY_KEYS:
    matches = _gc.get_cities_by_name(key)
    if not matches:
        continue
    # matches is a list of {geonameid: city} dicts; take the largest.
    flat = [next(iter(m.values())) for m in matches]
    flat.sort(key=lambda c: int(c.get("population", 0)), reverse=True)
    top = flat[0]
    if top["geonameid"] in _seen_ids:
        continue
    _seen_ids.add(top["geonameid"])
    _default_cities_cache.append(_city_to_dict(top))

# Also index cities by id for fast lookup.
_city_by_id: Dict[str, Dict[str, Any]] = {str(c["geonameid"]): c for c in _raw_cities}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StatusCheckCreate(BaseModel):
    client_name: str


class City(BaseModel):
    id: str
    name: str
    country: str
    country_code: str
    latitude: float
    longitude: float
    timezone: str
    population: int = 0


class BirthData(BaseModel):
    name: str
    birth_date: str  # DD-MM-YYYY
    birth_time: str  # HH:MM (24h)
    city_id: str


class Activation(BaseModel):
    label: str
    longitude: float
    gate: int
    line: int


class BlueprintResponse(BaseModel):
    id: str
    name: str
    city: City
    birth_date: str
    birth_time: str
    type: str
    strategy: str
    authority: str
    inner_authority: Optional[str] = None
    authority_process: str
    profile: str
    defined_centers: List[str]
    defined_channels: List[List[int]]
    active_gates: List[int]
    personality: List[Activation]
    design: List[Activation]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@api_router.get("/")
async def root():
    return {"message": "Birthlight Human Design API"}


@api_router.get("/cities", response_model=List[City])
async def get_cities(q: Optional[str] = Query(default=None), limit: int = Query(default=20, ge=1, le=100)):
    """Search cities globally. Without `q` returns a curated default list."""
    if not q or not q.strip():
        return [City(**c) for c in _default_cities_cache[:limit]]
    needle = q.strip().lower()
    matches: List[Dict[str, Any]] = []
    for city in _raw_cities:
        if needle in city["name"].lower():
            matches.append(city)
    matches.sort(key=lambda c: (-int(c.get("population", 0)), c["name"]))
    return [City(**_city_to_dict(c)) for c in matches[:limit]]


@api_router.get("/cities/{city_id}", response_model=City)
async def get_city(city_id: str):
    city = _city_by_id.get(city_id)
    if city is None:
        raise HTTPException(status_code=404, detail="City not found")
    return City(**_city_to_dict(city))


@api_router.post("/blueprint", response_model=BlueprintResponse)
async def create_blueprint(payload: BirthData):
    city_raw = _city_by_id.get(payload.city_id)
    if city_raw is None:
        raise HTTPException(status_code=400, detail="City not found")
    city_dict = _city_to_dict(city_raw)

    if not payload.name or not payload.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")

    try:
        # Strict DD-MM-YYYY / HH:MM validation.
        datetime.strptime(f"{payload.birth_date} {payload.birth_time}", "%d-%m-%Y %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid birth date/time; use DD-MM-YYYY and HH:MM")

    try:
        result = calculate_human_design(
            birth_date=payload.birth_date,
            birth_time=payload.birth_time,
            timezone_str=city_dict["timezone"],
        )
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=f"Calculation failed: {exc}")

    def to_activations(bundle: Dict[str, Dict[str, float]]) -> List[Activation]:
        return [
            Activation(
                label=label,
                longitude=round(bundle[label]["longitude"], 4),
                gate=int(bundle[label]["gate"]),
                line=int(bundle[label]["line"]),
            )
            for label in bundle
        ]

    return BlueprintResponse(
        id=str(uuid.uuid4()),
        name=payload.name.strip(),
        city=City(**city_dict),
        birth_date=payload.birth_date,
        birth_time=payload.birth_time,
        type=result["type"],
        strategy=result["strategy"],
        authority=result["authority"],
        inner_authority=result["inner_authority"],
        authority_process=result["authority_process"],
        profile=result["profile"],
        defined_centers=list(result["defined_centers"]),
        defined_channels=[list(pair) for pair in result["defined_channels"]],
        active_gates=list(result["active_gates"]),
        personality=to_activations(result["personality"]),
        design=to_activations(result["design"]),
    )


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.dict())
    await db.status_checks.insert_one(status_obj.dict())
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    rows = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    return [StatusCheck(**row) for row in rows]


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
