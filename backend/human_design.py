"""
Human Design blueprint calculation engine.

Strict specification:
- Uses `pyswisseph` (imported as `swisseph as swe`) for all planetary longitudes.
- Uses `swe.TRUE_NODE` for the North Node (South Node = North + 180 deg).
- 13 activations per side: Sun, Earth, Moon, North Node, South Node,
  Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto.
- Design chart is the moment the Sun was exactly 88 degrees of ecliptic
  longitude behind the birth Sun, located via binary search.
- Rave Mandala offset is 302 deg (Gate 41 starts at 302 deg tropical longitude).
- 64 gates x 6 lines, exactly 5.625 deg per gate, 0.9375 deg per line.
- 36 canonical channels, undirected graph BFS/DFS for center connectivity.
- Type / Authority determined by strict Human Design hierarchy.
- Profile = Personality Sun line / Design Sun line.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Set, Tuple
from zoneinfo import ZoneInfo

import swisseph as swe

# Rave Mandala sequence of 64 gates starting at 302 deg tropical longitude (Gate 41).
RAVE_MANDALA_GATES_FROM_41: List[int] = [
    41, 19, 13, 49, 30, 55, 37, 63,
    22, 36, 25, 17, 21, 51, 42, 3,
    27, 24, 2, 23, 8, 20, 16, 35,
    45, 12, 15, 52, 39, 53, 62, 56,
    31, 33, 7, 4, 29, 59, 40, 64,
    47, 6, 46, 18, 48, 57, 32, 50,
    28, 44, 1, 43, 14, 34, 9, 5,
    26, 11, 10, 58, 38, 54, 61, 60,
]

RAVE_MANDALA_OFFSET_DEG = 302.0
GATE_ARC = 360.0 / 64.0          # 5.625 deg
LINE_ARC = GATE_ARC / 6.0        # 0.9375 deg

# 36 canonical Human Design channels (undirected).
CHANNELS: List[Tuple[int, int]] = [
    (1, 8), (2, 14), (3, 60), (4, 63), (5, 15), (6, 59),
    (7, 31), (9, 52), (10, 20), (10, 34), (10, 57), (11, 56),
    (12, 22), (13, 33), (16, 48), (17, 62), (18, 58), (19, 49),
    (20, 34), (20, 57), (21, 45), (23, 43), (24, 61), (25, 51),
    (26, 44), (27, 50), (28, 38), (29, 46), (30, 41), (32, 54),
    (34, 57), (35, 36), (37, 40), (39, 55), (42, 53), (47, 64),
]

# Which two centers each channel connects.
CHANNEL_CENTERS: Dict[Tuple[int, int], Tuple[str, str]] = {
    (1, 8): ("G", "Throat"),
    (2, 14): ("G", "Sacral"),
    (3, 60): ("Sacral", "Root"),
    (4, 63): ("Ajna", "Head"),
    (5, 15): ("Sacral", "G"),
    (6, 59): ("SolarPlexus", "Sacral"),
    (7, 31): ("G", "Throat"),
    (9, 52): ("Sacral", "Root"),
    (10, 20): ("G", "Throat"),
    (10, 34): ("G", "Sacral"),
    (10, 57): ("G", "Spleen"),
    (11, 56): ("Ajna", "Throat"),
    (12, 22): ("Throat", "SolarPlexus"),
    (13, 33): ("G", "Throat"),
    (16, 48): ("Throat", "Spleen"),
    (17, 62): ("Ajna", "Throat"),
    (18, 58): ("Spleen", "Root"),
    (19, 49): ("Root", "SolarPlexus"),
    (20, 34): ("Throat", "Sacral"),
    (20, 57): ("Throat", "Spleen"),
    (21, 45): ("Heart", "Throat"),
    (23, 43): ("Throat", "Ajna"),
    (24, 61): ("Ajna", "Head"),
    (25, 51): ("G", "Heart"),
    (26, 44): ("Heart", "Spleen"),
    (27, 50): ("Sacral", "Spleen"),
    (28, 38): ("Spleen", "Root"),
    (29, 46): ("Sacral", "G"),
    (30, 41): ("SolarPlexus", "Root"),
    (32, 54): ("Spleen", "Root"),
    (34, 57): ("Sacral", "Spleen"),
    (35, 36): ("Throat", "SolarPlexus"),
    (37, 40): ("SolarPlexus", "Heart"),
    (39, 55): ("Root", "SolarPlexus"),
    (42, 53): ("Sacral", "Root"),
    (47, 64): ("Ajna", "Head"),
}

MOTOR_CENTERS = {"Sacral", "SolarPlexus", "Heart", "Root"}

# Ordered list of 13 activations calculated for both Personality and Design.
# ("label", planetary_body_or_None). None -> derived (Earth = Sun+180, South Node = North+180).
ACTIVATION_BODIES: List[Tuple[str, object]] = [
    ("Sun", swe.SUN),
    ("Earth", "SUN_OPPOSITE"),
    ("Moon", swe.MOON),
    ("NorthNode", swe.TRUE_NODE),
    ("SouthNode", "NODE_OPPOSITE"),
    ("Mercury", swe.MERCURY),
    ("Venus", swe.VENUS),
    ("Mars", swe.MARS),
    ("Jupiter", swe.JUPITER),
    ("Saturn", swe.SATURN),
    ("Uranus", swe.URANUS),
    ("Neptune", swe.NEPTUNE),
    ("Pluto", swe.PLUTO),
]

# Initialise Swiss Ephemeris with the built-in Moshier fallback (no external files required).
swe.set_ephe_path("")


def _longitude(julian_day: float, body: int) -> float:
    """Return the tropical ecliptic longitude in degrees [0, 360)."""
    result = swe.calc_ut(julian_day, body)
    return float(result[0][0]) % 360.0


def _sun_longitude(julian_day: float) -> float:
    return _longitude(julian_day, swe.SUN)


def design_julian_day(birth_jd: float) -> float:
    """Return the Julian Day when the Sun was exactly 88 degrees behind the birth Sun."""
    birth_sun = _sun_longitude(birth_jd)
    target = (birth_sun - 88.0) % 360.0

    # Sun moves ~0.985 deg/day so 88 deg takes ~89.3 days. Widen window generously.
    low = birth_jd - 95.0
    high = birth_jd - 82.0

    # Confirm invariant: at `low` the Sun has NOT yet reached target, at `high` it has.
    # If it doesn't, extend the window.
    for _ in range(10):
        low_ahead = (_sun_longitude(low) - target) % 360.0
        high_ahead = (_sun_longitude(high) - target) % 360.0
        # We want low_ahead > 180 (Sun below target still) and high_ahead < 180 (Sun already past).
        if low_ahead > 180.0 and high_ahead < 180.0:
            break
        low -= 5.0
        high += 5.0

    for _ in range(80):
        mid = (low + high) / 2.0
        ahead = (_sun_longitude(mid) - target) % 360.0
        if ahead < 180.0:
            high = mid
        else:
            low = mid

    return (low + high) / 2.0


def longitude_to_gate_line(longitude: float) -> Tuple[int, int]:
    """Map a tropical longitude to (gate, line) using the Rave Mandala."""
    shifted = (longitude - RAVE_MANDALA_OFFSET_DEG) % 360.0
    gate_index = int(shifted // GATE_ARC) % 64
    line_index = int((shifted - gate_index * GATE_ARC) // LINE_ARC) + 1
    line_index = min(6, max(1, line_index))
    return RAVE_MANDALA_GATES_FROM_41[gate_index], line_index


def _compute_activations(julian_day: float) -> Dict[str, Dict[str, float]]:
    """Return {label: {longitude, gate, line}} for the 13 activation bodies."""
    activations: Dict[str, Dict[str, float]] = {}
    sun_lon = _longitude(julian_day, swe.SUN)
    node_lon = _longitude(julian_day, swe.TRUE_NODE)
    for label, body in ACTIVATION_BODIES:
        if body == "SUN_OPPOSITE":
            lon = (sun_lon + 180.0) % 360.0
        elif body == "NODE_OPPOSITE":
            lon = (node_lon + 180.0) % 360.0
        else:
            lon = _longitude(julian_day, body)
        gate, line = longitude_to_gate_line(lon)
        activations[label] = {"longitude": lon, "gate": gate, "line": line}
    return activations


def _defined_centers_and_channels(active_gates: Set[int]) -> Tuple[Set[str], List[Tuple[int, int]], Dict[str, Set[str]]]:
    defined_channels = [pair for pair in CHANNELS if pair[0] in active_gates and pair[1] in active_gates]
    centers: Set[str] = set()
    graph: Dict[str, Set[str]] = {}
    for pair in defined_channels:
        a, b = CHANNEL_CENTERS[pair]
        centers.update((a, b))
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)
    return centers, defined_channels, graph


def _bfs_reaches(graph: Dict[str, Set[str]], start: str, target: str) -> bool:
    if start not in graph or target not in graph:
        return False
    seen = {start}
    stack = [start]
    while stack:
        node = stack.pop()
        if node == target:
            return True
        for neighbour in graph.get(node, ()):
            if neighbour not in seen:
                seen.add(neighbour)
                stack.append(neighbour)
    return False


def _determine_type(centers: Set[str], graph: Dict[str, Set[str]]) -> str:
    if not centers:
        return "Reflector"
    sacral = "Sacral" in centers
    motor_to_throat = any(
        m in centers and "Throat" in centers and _bfs_reaches(graph, m, "Throat")
        for m in MOTOR_CENTERS
    )
    if sacral and motor_to_throat:
        return "Manifesting Generator"
    if sacral:
        return "Generator"
    # Sacral undefined
    non_sacral_motor_to_throat = any(
        m in centers and "Throat" in centers and _bfs_reaches(graph, m, "Throat")
        for m in ("SolarPlexus", "Heart", "Root")
    )
    if non_sacral_motor_to_throat:
        return "Manifestor"
    return "Projector"


def _determine_authority(hd_type: str, centers: Set[str], graph: Dict[str, Set[str]]) -> str:
    if "SolarPlexus" in centers:
        return "Emotional"
    if "Sacral" in centers:
        return "Sacral"
    if "Spleen" in centers:
        return "Splenic"
    if "Heart" in centers and "Throat" in centers and _bfs_reaches(graph, "Heart", "Throat"):
        return "Ego"
    if "G" in centers and "Throat" in centers and _bfs_reaches(graph, "G", "Throat"):
        return "Self-Projected"
    if hd_type == "Reflector":
        return "Lunar"
    return "Mental"


def _strategy_for(hd_type: str) -> str:
    return {
        "Generator": "Wait to Respond",
        "Manifesting Generator": "Wait to Respond, then Inform",
        "Projector": "Wait for the Invitation",
        "Manifestor": "Inform before you act",
        "Reflector": "Wait a Lunar Cycle",
    }[hd_type]


def calculate_human_design(
    birth_date: str,
    birth_time: str,
    timezone_str: str,
) -> Dict[str, object]:
    """Main entry point.

    Args:
        birth_date: 'DD-MM-YYYY'
        birth_time: 'HH:MM' (24h local time)
        timezone_str: IANA timezone name, e.g. 'Asia/Jakarta'.
    """
    local_dt = datetime.strptime(f"{birth_date} {birth_time}", "%d-%m-%Y %H:%M").replace(
        tzinfo=ZoneInfo(timezone_str)
    )
    utc_dt = local_dt.astimezone(timezone.utc)
    hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    birth_jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour)

    design_jd = design_julian_day(birth_jd)

    personality = _compute_activations(birth_jd)
    design = _compute_activations(design_jd)

    active_gates: Set[int] = set()
    for act in personality.values():
        active_gates.add(int(act["gate"]))
    for act in design.values():
        active_gates.add(int(act["gate"]))

    centers, defined_channels, graph = _defined_centers_and_channels(active_gates)
    hd_type = _determine_type(centers, graph)
    authority = _determine_authority(hd_type, centers, graph)
    profile = f"{int(personality['Sun']['line'])}/{int(design['Sun']['line'])}"

    return {
        "type": hd_type,
        "authority": authority,
        "profile": profile,
        "strategy": _strategy_for(hd_type),
        "personality": personality,
        "design": design,
        "active_gates": sorted(active_gates),
        "defined_channels": [list(pair) for pair in defined_channels],
        "defined_centers": sorted(centers),
        "birth_jd": birth_jd,
        "design_jd": design_jd,
    }
