"""Regression tests for the Human Design calculation engine.

Charts provided by the user (NOT public celebrity charts). If ANY expected
value fails, the failure is reported with actual output + defined_centers +
active_gates so the user can debug. The algorithm is NOT tuned to force a
pass.
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

# User-provided charts with authoritative expected Type / Authority / Profile.
CHARTS = [
    {
        "label": "Yosep",
        "birth_date": "09-12-1976",
        "birth_time": "15:37",
        "timezone": "Asia/Jakarta",
        "expected": None,  # supplied without authoritative values yet
    },
    {
        "label": "Firza",
        "birth_date": "14-05-1978",
        "birth_time": "02:00",
        "timezone": "Asia/Jakarta",
        "expected": {
            "type": "Projector",
            "authority": "Self-Projected",
            "profile": "5/1",
            "inner_authority": "Self-Projected",
            "authority_process": "Self-Projected",
        },
    },
    {
        "label": "Tresna",
        "birth_date": "04-02-1997",
        "birth_time": "06:30",
        "timezone": "Asia/Jakarta",
        "expected": {
            "type": "Reflector",
            "authority": "Lunar",
            "profile": "3/5",
            "inner_authority": None,
            "authority_process": "Lunar",
        },
    },
    {
        "label": "Delicia",
        "birth_date": "06-10-2008",
        "birth_time": "07:15",
        "timezone": "Asia/Jakarta",
        "expected": {
            "type": "Manifestor",
            "authority": "Emotional",
            "profile": "4/6",
            "inner_authority": "Emotional",
            "authority_process": "Emotional",
        },
    },
    {
        # User provided the triple "Manifesting Generator / Emotional / 4/6"
        # without a matching name/birth data. Kept as an unfilled slot.
        "label": "Chart 5 (birth data pending)",
        "birth_date": None,
        "birth_time": None,
        "timezone": None,
        "expected": {"type": "Manifesting Generator", "authority": "Emotional", "profile": "4/6"},
    },
]


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
    diff = result["birth_jd"] - result["design_jd"]
    assert 82.0 <= diff <= 95.0, f"design offset out of range: {diff:.3f} days"
    for pair in result["defined_channels"]:
        key = tuple(pair)
        assert key in CHANNEL_CENTERS, f"unknown channel {key}"
    # Reflector <=> inner_authority is None.
    if result["type"] == "Reflector":
        assert result["inner_authority"] is None
        assert result["authority_process"] == "Lunar"


def test_structural_invariants():
    assert len(RAVE_MANDALA_GATES_FROM_41) == 64
    assert len(set(RAVE_MANDALA_GATES_FROM_41)) == 64
    assert set(RAVE_MANDALA_GATES_FROM_41) == set(range(1, 65))
    assert len(CHANNELS) == 36
    assert len(CHANNEL_CENTERS) == 36


def _run_chart(chart):
    if chart["birth_date"] is None:
        print(f"{chart['label']:<40} SKIP (no birth data supplied)")
        return None
    result = calculate_human_design(
        birth_date=chart["birth_date"],
        birth_time=chart["birth_time"],
        timezone_str=chart["timezone"],
    )
    _basic_invariants(result)
    actual = {
        "type": result["type"],
        "authority": result["authority"],
        "profile": result["profile"],
        "inner_authority": result["inner_authority"],
        "authority_process": result["authority_process"],
    }
    print(
        f"{chart['label']:<40} -> {actual['type']:<22} {actual['authority']:<16} {actual['profile']:<6} "
        f"IA={actual['inner_authority']}  process={actual['authority_process']}"
    )
    return result, actual


def test_charts_all_compute():
    print()
    failures = []
    for chart in CHARTS:
        outcome = _run_chart(chart)
        if outcome is None:
            continue
        result, actual = outcome
        exp = chart.get("expected")
        if not exp:
            continue
        mismatch = {k: (actual.get(k), v) for k, v in exp.items() if actual.get(k) != v}
        if mismatch:
            failures.append((chart["label"], mismatch, result))

    if failures:
        print("\n=== FAILURES (actual vs expected) ===")
        for label, mismatch, result in failures:
            print(f"\n{label}:")
            for k, (got, expected) in mismatch.items():
                print(f"  {k:<20} got={got!r:<30} expected={expected!r}")
            print(f"  defined_centers  : {result['defined_centers']}")
            print(f"  defined_channels : {result['defined_channels']}")
            print(f"  active_gates     : {result['active_gates']}")
            print(f"  personality Sun  : gate={result['personality']['Sun']['gate']} line={result['personality']['Sun']['line']} lon={result['personality']['Sun']['longitude']:.4f}")
            print(f"  design Sun       : gate={result['design']['Sun']['gate']} line={result['design']['Sun']['line']} lon={result['design']['Sun']['longitude']:.4f}")
            print(f"  birth_jd={result['birth_jd']:.6f}  design_jd={result['design_jd']:.6f}  diff={result['birth_jd']-result['design_jd']:.4f} days")
        raise AssertionError(f"{len(failures)} chart(s) failed. See report above.")


if __name__ == "__main__":
    test_structural_invariants()
    test_charts_all_compute()
    print("\nAll regression tests passed.")
