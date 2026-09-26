#!/usr/bin/env python3
"""Local ops dashboard. Planning assist only. Stage 1 worms remain the spend source of record."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import engine
import store

PACKAGE = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("OPS_DATA_DIR", PACKAGE / "data"))
BOOK = store.Book(DATA_DIR / "forwards.sqlite")

app = FastAPI(title="Loop ops forward dashboard", docs_url=None, redoc_url=None)

BLOCK_MESSAGE = (
    "Stop. This promise would take worms or birds out of the breeding herd. "
    "The sale is blocked."
)


class HerdIn(BaseModel):
    n0: float = Field(gt=0)
    n_start: float | None = None
    n_safety: float | None = None
    reliability: float = 0.9
    horizon_months: int = 12


class ForwardIn(BaseModel):
    buyer: str
    species: str
    qty: float = Field(gt=0)
    unit: str | None = None
    delivery_month: int = Field(ge=1, le=engine.MAX_MONTH)
    price_usd: float | None = Field(default=None, ge=0)
    status: str = "promised"
    herd: HerdIn | None = None


class ReverseIn(BaseModel):
    species: str
    n0: float = Field(gt=0)
    n_start: float | None = None
    n_safety: float | None = None
    target_income_usd: float = Field(ge=0)
    months: int = Field(ge=1, le=engine.MAX_MONTH)
    reliability: float = 0.9


def _check_species(species: str) -> engine.SpeciesModel:
    if species not in engine.SPECIES:
        raise HTTPException(status_code=400, detail="Species must be worms or quail.")
    return engine.SPECIES[species]


def _herd_for(species: str, herd: HerdIn | None) -> dict:
    saved = BOOK.herd(species)
    if herd is None:
        return saved
    return BOOK.save_herd(species, herd.model_dump())


def _normalize(body: ForwardIn, herd: dict, exclude_id: int | None = None) -> dict:
    model = _check_species(body.species)
    if body.status not in store.STATUSES:
        raise HTTPException(status_code=400, detail="Status must be draft, promised, delivered, or cancelled.")
    if body.buyer.strip() == "":
        raise HTTPException(status_code=400, detail="Add the buyer's name.")
    price = body.price_usd
    if price is None:
        price = engine.price_quote(body.species, body.delivery_month)["F_prelim"]
    row = {
        "buyer": body.buyer.strip(),
        "species": body.species,
        "qty": float(body.qty),
        "unit": body.unit or model.unit,
        "delivery_month": int(body.delivery_month),
        "price_usd": float(price),
        "status": body.status,
    }
    if row["unit"] != model.unit:
        raise HTTPException(status_code=400, detail=f"Unit for {model.label} is {model.unit}.")
    if row["status"] in ("draft", "promised"):
        others = [item for item in BOOK.list_forwards() if item["id"] != exclude_id]
        safe = engine.booking_is_safe(
            body.species,
            herd["n0"],
            others + [row],
            n_start=herd.get("n_start"),
            n_safety=herd.get("n_safety"),
            reliability=float(herd.get("reliability") or 0.9),
        )
        if not safe:
            raise HTTPException(status_code=409, detail=BLOCK_MESSAGE)
    return row


@app.get("/")
def index() -> FileResponse:
    return FileResponse(PACKAGE / "static" / "index.html")


@app.get("/api/meta")
def meta() -> dict:
    return {
        "stage_gate": "Stage 1 worms are the only active spend. This screen does not approve Stage 2–5 purchases.",
        "r_inf": engine.R_INF,
        "r_inf_as_of": "2026-08",
        "r_prime": engine.R_PRIME,
        "r_prime_as_of": "2026-09-24",
        "fairness": engine.FAIRNESS,
        "formula": (
            "E[P(T)] = E[P0] * (1+r_inf)^T; "
            "F_prelim = 0.9 * E[P(T)] / (1+r_prime)^T"
        ),
        "species": {key: model.to_public() for key, model in engine.SPECIES.items()},
        "p90_plain": (
            "Safe to sell (P90) is the amount you can promise and still have the breeding herd "
            "in at least 90 of 100 simulated futures. It is not the middle outcome."
        ),
    }


@app.get("/api/forwards")
def list_forwards() -> list[dict]:
    return BOOK.list_forwards()


@app.post("/api/forwards")
def create_forward(body: ForwardIn) -> dict:
    herd = _herd_for(body.species, body.herd)
    row = _normalize(body, herd)
    return BOOK.insert_forward(row)


@app.put("/api/forwards/{row_id}")
def update_forward(row_id: int, body: ForwardIn) -> dict:
    if BOOK.get_forward(row_id) is None:
        raise HTTPException(status_code=404, detail="That promise is not in the book.")
    herd = _herd_for(body.species, body.herd)
    row = _normalize(body, herd, exclude_id=row_id)
    updated = BOOK.update_forward(row_id, row)
    if updated is None:
        raise HTTPException(status_code=404, detail="That promise is not in the book.")
    return updated


@app.delete("/api/forwards/{row_id}")
def delete_forward(row_id: int) -> dict:
    if not BOOK.delete_forward(row_id):
        raise HTTPException(status_code=404, detail="That promise is not in the book.")
    return {"ok": True}


@app.post("/api/sell-limit")
def post_sell_limit(body: HerdIn, species: str = "worms") -> dict:
    _check_species(species)
    herd = BOOK.save_herd(species, body.model_dump())
    return engine.sell_limit(
        species,
        herd["n0"],
        BOOK.list_forwards(),
        n_start=herd.get("n_start"),
        n_safety=herd.get("n_safety"),
        reliability=float(herd.get("reliability") or 0.9),
        horizon_months=int(herd.get("horizon_months") or 12),
    )


@app.post("/api/reverse")
def post_reverse(body: ReverseIn) -> dict:
    _check_species(body.species)
    return engine.reverse_income(
        body.species,
        body.n0,
        body.target_income_usd,
        body.months,
        reliability=body.reliability,
        n_start=body.n_start,
        n_safety=body.n_safety,
    )


@app.get("/api/price")
def get_price(species: str = "worms", delivery_month: int = 12) -> dict:
    _check_species(species)
    if delivery_month < 1 or delivery_month > engine.MAX_MONTH:
        raise HTTPException(status_code=400, detail=f"Delivery month must be 1..{engine.MAX_MONTH}.")
    return engine.price_quote(species, delivery_month)


@app.get("/api/dashboard")
def dashboard(species: str = "worms") -> dict:
    _check_species(species)
    herd = BOOK.herd(species)
    limit = engine.sell_limit(
        species,
        herd["n0"],
        BOOK.list_forwards(),
        n_start=herd.get("n_start"),
        n_safety=herd.get("n_safety"),
        reliability=float(herd.get("reliability") or 0.9),
        horizon_months=int(herd.get("horizon_months") or 12),
    )
    return {"herd": herd, "forwards": BOOK.list_forwards(), "sell_limit": limit, "meta": meta()}


def main() -> None:
    import uvicorn

    host = os.environ.get("OPS_HOST", "127.0.0.1")
    port = int(os.environ.get("OPS_PORT", "8765"))
    uvicorn.run("app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
