#!/usr/bin/env python3
"""Smoke the reverse tool and the local forward book. Does not touch the ops database."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

os.environ["OPS_SEED_DEMO"] = "0"

import app as app_module  # noqa: E402
from engine import reverse_income  # noqa: E402

OUT = Path(__file__).resolve().parent / "results" / "reverse_smoke.json"


def _request(base: str, method: str, path: str, payload: dict | None = None) -> tuple[int, dict | list]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(base + path, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as res:
            body = res.read().decode("utf-8")
            return res.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8")
        return err.code, json.loads(raw) if raw else {}


def main() -> None:
    result = reverse_income("worms", n0=16500, target_income_usd=2000, months=12, reliability=0.10)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    tmp = Path(tempfile.mkdtemp(prefix="ops-dashboard-"))
    httpd = app_module.serve("127.0.0.1", 0, tmp, seed_demo=False)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    try:
        empty_status, empty = _request(
            base,
            "POST",
            "/api/sell-limit?species=worms",
            {"n0": 16500, "reliability": 0.10, "horizon_months": 12},
        )
        assert empty_status == 200, empty
        room_before = empty["remaining_room_units"]

        created_status, created = _request(
            base,
            "POST",
            "/api/forwards",
            {
                "buyer": "North farm",
                "species": "worms",
                "qty": 10,
                "delivery_month": 12,
                "status": "promised",
                "herd": {"n0": 16500, "reliability": 0.10, "horizon_months": 12},
            },
        )
        assert created_status == 200, created
        row_id = created["id"]

        listed_status, listed = _request(base, "GET", "/api/forwards")
        assert listed_status == 200
        assert any(row["id"] == row_id for row in listed)
        assert (tmp / "forwards.sqlite").exists()

        after_status, after = _request(
            base,
            "POST",
            "/api/sell-limit?species=worms",
            {"n0": 16500, "reliability": 0.10, "horizon_months": 12},
        )
        assert after_status == 200, after
        room_after = after["remaining_room_units"]
        assert room_after < room_before - 5, (room_before, room_after)

        bigger_status, bigger = _request(
            base,
            "POST",
            "/api/sell-limit?species=worms",
            {"n0": 30000, "reliability": 0.10, "horizon_months": 12},
        )
        assert bigger_status == 200, bigger
        assert bigger["safe_to_sell_units"] > after["safe_to_sell_units"]

        _request(
            base,
            "POST",
            "/api/sell-limit?species=worms",
            {"n0": 16500, "reliability": 0.10, "horizon_months": 12},
        )
        blocked_status, blocked = _request(
            base,
            "POST",
            "/api/forwards",
            {
                "buyer": "Too much",
                "species": "worms",
                "qty": 5000,
                "delivery_month": 12,
                "status": "promised",
                "herd": {"n0": 16500, "reliability": 0.10, "horizon_months": 12},
            },
        )
        assert blocked_status == 409, blocked
        assert "breeding herd" in blocked["detail"]

        edited_status, edited = _request(
            base,
            "PUT",
            f"/api/forwards/{row_id}",
            {
                "buyer": "North farm",
                "species": "worms",
                "qty": 8,
                "delivery_month": 12,
                "status": "promised",
                "herd": {"n0": 16500, "reliability": 0.10, "horizon_months": 12},
            },
        )
        assert edited_status == 200, edited
        assert edited["qty"] == 8

        deleted_status, _deleted = _request(base, "DELETE", f"/api/forwards/{row_id}")
        assert deleted_status == 200
        _status, remaining = _request(base, "GET", "/api/forwards")
        assert remaining == []

        page_status, _page = 200, None
        with urllib.request.urlopen(base + "/") as res:
            page_status = res.status
            html = res.read().decode("utf-8")
        assert page_status == 200 and "Forward book" in html and "Cascade sale" in html
        status, cascade = _request(base, "POST", "/api/cascade-impact", {
            "quail_males": 24,
            "quail_females": 72,
            "worm_headcount": 250000,
            "species": "quail",
            "n": 16,
            "month": 4,
            "fish_n": 0,
        })
        assert status == 200
        assert cascade["status"] in ("ok", "warn")
        assert cascade["surplus"]["excess_lb_at_sale"] > 0
        assert cascade["direct"]["Ne_after"] >= 50
        status, refused = _request(base, "POST", "/api/cascade-impact", {
            "quail_males": 24,
            "quail_females": 72,
            "worm_headcount": 250000,
            "species": "quail",
            "n": 40,
            "month": 4,
        })
        assert status == 200 and refused["status"] == "refuse"
    finally:
        httpd.shutdown()

    assert result["n0"] == 16500
    assert result["months"] == 12
    assert result["reliability"] == 0.10
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
