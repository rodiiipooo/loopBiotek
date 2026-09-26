"""Local SQLite book for prepaid forwards. No network."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_HERD = {
    "worms": {"n0": 16500, "n_start": None, "n_safety": None, "reliability": 0.9, "horizon_months": 12},
    "quail": {"n0": 20, "n_start": None, "n_safety": None, "reliability": 0.9, "horizon_months": 12},
}

STATUSES = ("draft", "promised", "delivered", "cancelled")


class Book:
    def __init__(self, path: Path, seed_demo: bool = True) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init()
        if seed_demo:
            self.seed_demo()

    def seed_demo(self) -> None:
        """Load the shipped sample herd and one draft promise into an empty book."""
        if self.list_forwards():
            return
        existing = self._conn.execute("SELECT COUNT(*) AS c FROM settings").fetchone()["c"]
        if existing:
            return
        demo_path = Path(__file__).resolve().parent / "demo_config.json"
        demo = json.loads(demo_path.read_text(encoding="utf-8"))
        for species, herd in demo["herds"].items():
            self.save_herd(species, herd)
        import engine

        for row in demo["forwards"]:
            price = row.get("price_usd")
            if price is None:
                price = engine.price_quote(row["species"], int(row["delivery_month"]))["F_prelim"]
            self.insert_forward(
                {
                    "buyer": row["buyer"],
                    "species": row["species"],
                    "qty": float(row["qty"]),
                    "unit": row["unit"],
                    "delivery_month": int(row["delivery_month"]),
                    "price_usd": float(price),
                    "status": row["status"],
                }
            )

    def _init(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS forwards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer TEXT NOT NULL,
                species TEXT NOT NULL,
                qty REAL NOT NULL,
                unit TEXT NOT NULL,
                delivery_month INTEGER NOT NULL,
                price_usd REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def list_forwards(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM forwards ORDER BY delivery_month, id"
        ).fetchall()
        return [dict(row) for row in rows]

    def get_forward(self, row_id: int) -> dict | None:
        row = self._conn.execute("SELECT * FROM forwards WHERE id = ?", (row_id,)).fetchone()
        return None if row is None else dict(row)

    def insert_forward(self, row: dict) -> dict:
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        cur = self._conn.execute(
            """
            INSERT INTO forwards (buyer, species, qty, unit, delivery_month, price_usd, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["buyer"],
                row["species"],
                row["qty"],
                row["unit"],
                row["delivery_month"],
                row["price_usd"],
                row["status"],
                now,
            ),
        )
        self._conn.commit()
        saved = self.get_forward(int(cur.lastrowid))
        assert saved is not None
        return saved

    def update_forward(self, row_id: int, row: dict) -> dict | None:
        existing = self.get_forward(row_id)
        if existing is None:
            return None
        self._conn.execute(
            """
            UPDATE forwards
               SET buyer = ?, species = ?, qty = ?, unit = ?, delivery_month = ?, price_usd = ?, status = ?
             WHERE id = ?
            """,
            (
                row["buyer"],
                row["species"],
                row["qty"],
                row["unit"],
                row["delivery_month"],
                row["price_usd"],
                row["status"],
                row_id,
            ),
        )
        self._conn.commit()
        return self.get_forward(row_id)

    def delete_forward(self, row_id: int) -> bool:
        cur = self._conn.execute("DELETE FROM forwards WHERE id = ?", (row_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def herd(self, species: str) -> dict:
        row = self._conn.execute("SELECT value FROM settings WHERE key = ?", (f"herd:{species}",)).fetchone()
        base = dict(DEFAULT_HERD.get(species, DEFAULT_HERD["worms"]))
        if row is None:
            return base
        saved = json.loads(row["value"])
        base.update(saved)
        return base

    def save_herd(self, species: str, herd: dict) -> dict:
        current = self.herd(species)
        for key in ("n0", "n_start", "n_safety", "reliability", "horizon_months"):
            if key in herd:
                current[key] = herd[key]
        self._conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (f"herd:{species}", json.dumps(current)),
        )
        self._conn.commit()
        return current
