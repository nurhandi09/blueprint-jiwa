"""Regression tests for the Human Design calculation engine.

These charts are used to verify structural correctness of the engine. All 5
charts must produce a valid Type / Authority / Profile without exceptions and
the strict internal invariants must hold.

If you have authoritative expected values (e.g. from Jovian Archive or Human
Design International), fill them into `EXPECTED` below and the tests will
compare them exactly.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from human_design import (
    CHANNELS,
    CHANNEL_CENTERS,
    RAVE_MANDALA_GATES_FROM_41,
    calculate_human_design,
)

VALID_TYPES = {"Generator", "Manifesting Generator", "Projector", "Manifestor", "Reflector"}
VALID_AUTHORITIES = {"Emotional", "Sacral", "Splenic", "Ego", "Self-Projected", "Mental", "Lunar"}

# Reference charts. Fill EXPECTED with (type, authority, profile) tuples when you
# have authoritative values to compare against.
CHARTS = [
    {
        "label": "Yosep (Bandung)",
        "birth_date": "09-12-1976",
        "birth_time": "15:37",
        "timezone": "Asia/Jakarta",
    },
    {
        "label": "Ra Uru Hu (founder, Merv 1948)",
        "birth_date": "09-04-1948",
        "birth_time": "12:15",
        "timezone": "Asia/Ashgabat",
    },
    {
        "label": "Barack Obama (Honolulu 1961)",
        "birth_date": "04-08-1961",
        "birth_time": "19:24",
        "timezone": "Pacific/Honolulu",
    },
    {
        "label": "Oprah Winfrey (Kosciusko MS 1954)",
        "birth_date": "29-01-1954",
        "birth_time": "04:30",
        "timezone": "America/Chicago",
    },
    {
        "label": "Nelson Mandela (Mvezo 1918)",
        "birth_date": "18-07-1918",
        "birth_time": "14:54",
        "timezone": "Africa/Johannesburg",
    },
]

# Optional authoritative expected values (fill when known).
EXPECTED = {
    # "Ra Uru Hu (founder, Merv 1948)": {"type": "Manifestor", "authority": "Splenic", "profile": "5/1"},
    # "Barack Obama (Honolulu 1961)":   {"type": "Manifesting Generator", "authority": "Emotional", "profile": "6/2"},
    # "Oprah Winfrey (Kosciusko MS 1954)": {"type": "Manifesting Generator", "authority": "Sacral", "profile": "3/5"},
    # "Nelson Mandela (Mvezo 1918)":    {"type": "Projector", "authority": "Splenic", "profile": "1/3"},
}


def _basic_invariants(result):
    assert result["type"] in VALID_TYPES, result["type"]
    assert result["authority"] in VALID_AUTHORITIES, result["authority"]
    p, d = result["profile"].split("/")
    assert 1 <= int(p) <= 6 and 1 <= int(d) <= 6
    for name in ("personality", "design"):
        assert len(result[name]) == 13, f"{name} has {len(result[name])} entries"
        for act in result[name].values():
            assert 1 <= int(act["gate"]) <= 64
            assert 1 <= int(act["line"]) <= 6
            assert 0.0 <= float(act["longitude"]) < 360.0
    # Design chart should be 82-95 days before birth (88 deg solar arc).
    diff = result["birth_jd"] - result["design_jd"]
    assert 82.0 <= diff <= 95.0, f"design offset out of range: {diff:.3f} days"
    # Every defined channel must be in the canonical list.
    for pair in result["defined_channels"]:
        key = tuple(pair)
        assert key in CHANNEL_CENTERS, f"unknown channel {key}"


def test_structural_invariants():
    assert len(RAVE_MANDALA_GATES_FROM_41) == 64
    assert len(set(RAVE_MANDALA_GATES_FROM_41)) == 64
    assert set(RAVE_MANDALA_GATES_FROM_41) == set(range(1, 65))
    assert len(CHANNELS) == 36
    assert len(CHANNEL_CENTERS) == 36


def test_charts_all_compute():
    print()
    for chart in CHARTS:
        result = calculate_human_design(
            birth_date=chart["birth_date"],
            birth_time=chart["birth_time"],
            timezone_str=chart["timezone"],
        )
        _basic_invariants(result)
        print(
            f"{chart['label']:<45} "
            f"-> {result['type']:<22} {result['authority']:<15} {result['profile']}"
        )
        exp = EXPECTED.get(chart["label"])
        if exp:
            assert result["type"] == exp["type"], (chart["label"], result["type"], exp)
            assert result["authority"] == exp["authority"], (chart["label"], result["authority"], exp)
            assert result["profile"] == exp["profile"], (chart["label"], result["profile"], exp)


if __name__ == "__main__":
    test_structural_invariants()
    test_charts_all_compute()
    print("All regression tests passed.")
