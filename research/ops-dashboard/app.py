#!/usr/bin/env python3
"""Local ops dashboard. Standard library only. Stage 1 worms remain the spend source of record."""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import engine
import store

PACKAGE = Path(__file__).resolve().parent

BLOCK_MESSAGE = (
    "Stop. This promise would take worms or birds out of the breeding herd. "
    "The sale is blocked."
)


class ApiError(Exception):
    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


def _check_species(species: str) -> engine.SpeciesModel:
    if species not in engine.SPECIES:
        raise ApiError(400, "Species must be worms or quail.")
    return engine.SPECIES[species]


def _num(value, name: str, *, minimum: float | None = None, maximum: float | None = None) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ApiError(400, f"{name} must be a number.") from None
    if minimum is not None and number < minimum:
        raise ApiError(400, f"{name} is too small.")
    if maximum is not None and number > maximum:
        raise ApiError(400, f"{name} is too large.")
    return number


def _herd_from_body(body: dict) -> dict:
    herd = body.get("herd") if isinstance(body.get("herd"), dict) else body
    if "n0" not in herd:
        raise ApiError(400, "Starting herd is required.")
    reliability = herd.get("reliability", 0.9)
    horizon = herd.get("horizon_months", 12)
    return {
        "n0": _num(herd.get("n0"), "Starting herd", minimum=0.0001),
        "n_start": None if herd.get("n_start") in (None, "") else _num(herd.get("n_start"), "Planned start", minimum=0),
        "n_safety": None if herd.get("n_safety") in (None, "") else _num(herd.get("n_safety"), "Safety reserve", minimum=0),
        "reliability": _num(reliability, "How sure", minimum=0.5, maximum=0.999),
        "horizon_months": int(_num(horizon, "Month", minimum=1, maximum=engine.MAX_MONTH)),
    }


def _normalize(book: store.Book, body: dict, herd: dict, exclude_id: int | None = None) -> dict:
    model = _check_species(str(body.get("species", "")))
    status = str(body.get("status", "promised"))
    if status not in store.STATUSES:
        raise ApiError(400, "Status must be draft, promised, delivered, or cancelled.")
    buyer = str(body.get("buyer", "")).strip()
    if buyer == "":
        raise ApiError(400, "Add the buyer's name.")
    month = int(_num(body.get("delivery_month"), "Delivery month", minimum=1, maximum=engine.MAX_MONTH))
    price = body.get("price_usd")
    if price is None or price == "":
        price = engine.price_quote(model.key, month)["F_prelim"]
    else:
        price = _num(price, "Price", minimum=0)
    unit = body.get("unit") or model.unit
    if unit != model.unit:
        raise ApiError(400, f"Unit for {model.label} is {model.unit}.")
    row = {
        "buyer": buyer,
        "species": model.key,
        "qty": _num(body.get("qty"), "Quantity", minimum=0.0001),
        "unit": unit,
        "delivery_month": month,
        "price_usd": float(price),
        "status": status,
    }
    if status in ("draft", "promised"):
        others = [item for item in book.list_forwards() if item["id"] != exclude_id]
        safe = engine.booking_is_safe(
            model.key,
            herd["n0"],
            others + [row],
            n_start=herd.get("n_start"),
            n_safety=herd.get("n_safety"),
            reliability=float(herd.get("reliability") or 0.9),
        )
        if not safe:
            raise ApiError(409, BLOCK_MESSAGE)
    return row


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


def sell_limit_for(book: store.Book, species: str, herd: dict) -> dict:
    saved = book.save_herd(species, herd)
    return engine.sell_limit(
        species,
        saved["n0"],
        book.list_forwards(),
        n_start=saved.get("n_start"),
        n_safety=saved.get("n_safety"),
        reliability=float(saved.get("reliability") or 0.9),
        horizon_months=int(saved.get("horizon_months") or 12),
    )


def dashboard_for(book: store.Book, species: str) -> dict:
    _check_species(species)
    herd = book.herd(species)
    limit = engine.sell_limit(
        species,
        herd["n0"],
        book.list_forwards(),
        n_start=herd.get("n_start"),
        n_safety=herd.get("n_safety"),
        reliability=float(herd.get("reliability") or 0.9),
        horizon_months=int(herd.get("horizon_months") or 12),
    )
    return {"herd": herd, "forwards": book.list_forwards(), "sell_limit": limit, "meta": meta()}


def make_handler(book: store.Book):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:
            sys.stderr.write("%s - %s\n" % (self.log_date_time_string(), fmt % args))

        def _send(self, status: int, payload, content_type: str = "application/json; charset=utf-8") -> None:
            if not isinstance(payload, (bytes, bytearray)):
                payload = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _body(self) -> dict:
            length = int(self.headers.get("Content-Length", "0") or 0)
            raw = self.rfile.read(length) if length else b""
            if not raw:
                return {}
            try:
                parsed = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                raise ApiError(400, "That was not valid JSON.") from None
            if not isinstance(parsed, dict):
                raise ApiError(400, "The request body must be an object.")
            return parsed

        def _query(self) -> dict[str, str]:
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            return {key: values[-1] for key, values in qs.items()}

        def _dispatch(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            method = self.command
            try:
                if method == "GET" and path == "/":
                    page = (PACKAGE / "static" / "index.html").read_bytes()
                    self._send(200, page, "text/html; charset=utf-8")
                    return
                if method == "GET" and path == "/api/meta":
                    self._send(200, meta())
                    return
                if method == "GET" and path == "/api/forwards":
                    self._send(200, book.list_forwards())
                    return
                if method == "GET" and path == "/api/price":
                    qs = self._query()
                    species = qs.get("species", "worms")
                    _check_species(species)
                    month = int(_num(qs.get("delivery_month", "12"), "Delivery month", minimum=1, maximum=engine.MAX_MONTH))
                    self._send(200, engine.price_quote(species, month))
                    return
                if method == "GET" and path == "/api/dashboard":
                    species = self._query().get("species", "worms")
                    self._send(200, dashboard_for(book, species))
                    return
                if method == "POST" and path == "/api/forwards":
                    body = self._body()
                    species = str(body.get("species", ""))
                    _check_species(species)
                    herd = book.save_herd(species, _herd_from_body(body))
                    row = _normalize(book, body, herd)
                    self._send(200, book.insert_forward(row))
                    return
                if method == "POST" and path == "/api/sell-limit":
                    species = self._query().get("species", "worms")
                    _check_species(species)
                    herd = _herd_from_body(self._body())
                    self._send(200, sell_limit_for(book, species, herd))
                    return
                if method == "POST" and path == "/api/reverse":
                    body = self._body()
                    species = str(body.get("species", ""))
                    _check_species(species)
                    months = int(_num(body.get("months"), "Month", minimum=1, maximum=engine.MAX_MONTH))
                    result = engine.reverse_income(
                        species,
                        _num(body.get("n0"), "Starting herd", minimum=0.0001),
                        _num(body.get("target_income_usd"), "Target income", minimum=0),
                        months,
                        reliability=_num(body.get("reliability", 0.9), "How sure", minimum=0.5, maximum=0.999),
                        n_start=None if body.get("n_start") in (None, "") else _num(body.get("n_start"), "Planned start", minimum=0),
                        n_safety=None if body.get("n_safety") in (None, "") else _num(body.get("n_safety"), "Safety reserve", minimum=0),
                    )
                    self._send(200, result)
                    return
                if method in ("PUT", "DELETE") and path.startswith("/api/forwards/"):
                    try:
                        row_id = int(path.rsplit("/", 1)[-1])
                    except ValueError:
                        raise ApiError(404, "That promise is not in the book.") from None
                    if book.get_forward(row_id) is None:
                        raise ApiError(404, "That promise is not in the book.")
                    if method == "DELETE":
                        book.delete_forward(row_id)
                        self._send(200, {"ok": True})
                        return
                    body = self._body()
                    species = str(body.get("species", ""))
                    _check_species(species)
                    herd = book.save_herd(species, _herd_from_body(body))
                    row = _normalize(book, body, herd, exclude_id=row_id)
                    updated = book.update_forward(row_id, row)
                    if updated is None:
                        raise ApiError(404, "That promise is not in the book.")
                    self._send(200, updated)
                    return
                raise ApiError(404, "Not found.")
            except ApiError as err:
                self._send(err.status, {"detail": err.detail})
            except ValueError as err:
                self._send(400, {"detail": str(err)})

        def do_GET(self) -> None:
            self._dispatch()

        def do_POST(self) -> None:
            self._dispatch()

        def do_PUT(self) -> None:
            self._dispatch()

        def do_DELETE(self) -> None:
            self._dispatch()

    return Handler


def serve(host: str, port: int, data_dir: Path, seed_demo: bool = True) -> ThreadingHTTPServer:
    book = store.Book(data_dir / "forwards.sqlite", seed_demo=seed_demo)
    httpd = ThreadingHTTPServer((host, port), make_handler(book))
    httpd.book_path = book.path  # type: ignore[attr-defined]
    return httpd


def main() -> None:
    if sys.version_info < (3, 10):
        sys.stderr.write(f"Python 3.10 or newer is required. This is {sys.version.split()[0]}.\n")
        raise SystemExit(1)
    host = os.environ.get("OPS_HOST", "127.0.0.1")
    port = int(os.environ.get("OPS_PORT", "8765"))
    data_dir = Path(os.environ.get("OPS_DATA_DIR", PACKAGE / "data"))
    seed = os.environ.get("OPS_SEED_DEMO", "1") != "0"
    httpd = serve(host, port, data_dir, seed_demo=seed)
    shown = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    print(f"Open http://{shown}:{port}")
    print(f"Data file: {httpd.book_path}")  # type: ignore[attr-defined]
    if host == "0.0.0.0":
        print("Also reachable from other devices on this network at this machine's address.")
    print("Stop with Ctrl-C.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        httpd.server_close()


if __name__ == "__main__":
    main()
