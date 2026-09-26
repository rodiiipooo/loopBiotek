#!/usr/bin/env python3
"""Smoke the reverse tool and the local forward book. Does not touch the ops database."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

# Point the app at a throwaway book before it is imported.
_TMP = Path(tempfile.mkdtemp(prefix="ops-dashboard-"))
os.environ["OPS_DATA_DIR"] = str(_TMP)

from fastapi.testclient import TestClient  # noqa: E402

import app as app_module  # noqa: E402
from engine import reverse_income  # noqa: E402

OUT = Path(__file__).resolve().parent / "results" / "reverse_smoke.json"


def main() -> None:
    result = reverse_income("worms", n0=16500, target_income_usd=2000, months=12, reliability=0.9)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    client = TestClient(app_module.app)
    empty = client.post(
        "/api/sell-limit?species=worms",
        json={"n0": 16500, "reliability": 0.9, "horizon_months": 12},
    )
    assert empty.status_code == 200, empty.text
    room_before = empty.json()["remaining_room_units"]

    created = client.post(
        "/api/forwards",
        json={
            "buyer": "North farm",
            "species": "worms",
            "qty": 10,
            "delivery_month": 12,
            "status": "promised",
            "herd": {"n0": 16500, "reliability": 0.9, "horizon_months": 12},
        },
    )
    assert created.status_code == 200, created.text
    row_id = created.json()["id"]

    listed = client.get("/api/forwards")
    assert listed.status_code == 200
    assert any(row["id"] == row_id for row in listed.json())
    db_file = Path(os.environ["OPS_DATA_DIR"]) / "forwards.sqlite"
    assert db_file.exists()

    after = client.post(
        "/api/sell-limit?species=worms",
        json={"n0": 16500, "reliability": 0.9, "horizon_months": 12},
    )
    room_after = after.json()["remaining_room_units"]
    assert room_after < room_before - 5, (room_before, room_after)

    bigger_herd = client.post(
        "/api/sell-limit?species=worms",
        json={"n0": 30000, "reliability": 0.9, "horizon_months": 12},
    )
    assert bigger_herd.json()["safe_to_sell_units"] > after.json()["safe_to_sell_units"]

    # Put the herd back so the block test uses 16,500.
    client.post(
        "/api/sell-limit?species=worms",
        json={"n0": 16500, "reliability": 0.9, "horizon_months": 12},
    )
    blocked = client.post(
        "/api/forwards",
        json={
            "buyer": "Too much",
            "species": "worms",
            "qty": 5000,
            "delivery_month": 12,
            "status": "promised",
            "herd": {"n0": 16500, "reliability": 0.9, "horizon_months": 12},
        },
    )
    assert blocked.status_code == 409, blocked.text
    assert "breeding herd" in blocked.json()["detail"]

    edited = client.put(
        f"/api/forwards/{row_id}",
        json={
            "buyer": "North farm",
            "species": "worms",
            "qty": 8,
            "delivery_month": 12,
            "status": "promised",
            "herd": {"n0": 16500, "reliability": 0.9, "horizon_months": 12},
        },
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["qty"] == 8

    deleted = client.delete(f"/api/forwards/{row_id}")
    assert deleted.status_code == 200
    assert client.get("/api/forwards").json() == []

    assert result["n0"] == 16500
    assert result["months"] == 12
    assert result["reliability"] == 0.9
    assert result["feasible"] is False
    assert result["lump_covers_target"] is True
    assert result["min_n0"] is not None
    assert result["later_month"] is not None
    assert result["f_prelim_usd_per_unit"] > 30

    print(
        f"monthly_cap={result['max_monthly_sell_units']} lb  "
        f"income_at_cap=${result['income_at_cap_usd']}  "
        f"feasible_monthly={result['feasible']}  "
        f"lump={result['lump_at_horizon_units']} lb  "
        f"lump_income=${result['lump_income_usd']}  "
        f"F_prelim=${result['f_prelim_usd_per_unit']:.4f}  "
        f"min_n0={result['min_n0']}  later_month={result['later_month']}"
    )
    print(f"wrote {OUT}")
    print(f"room {room_before:.2f} -> {room_after:.2f} lb after a 10 lb promise")


if __name__ == "__main__":
    main()
