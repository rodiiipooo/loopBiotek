#!/usr/bin/env python3
"""Starting quail flock for about $2,000 a month from month 2, on the P10 tail.

Stage 4 planning. The growth curve is the ops-dashboard ASSUMPTION stub.
The birds that must stay are the strict genetics floor. Feed is an
ASSUMPTION intake plus the synergy 2-week buffer. This does not buy birds,
worms, or plants, and it does not open Stage 2–5 spend.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import engine

_GENETICS = Path(__file__).resolve().parents[1] / "genetics"
if str(_GENETICS) not in sys.path:
    sys.path.insert(0, str(_GENETICS))

import reproduction as genetics  # noqa: E402

TARGET_USD = 2000.0
FIRST_MONTH = 2
HORIZON = 24
N0_CAP = 200_000.0
# ASSUMPTION. Not a measured ration. Adult Coturnix planning intake.
INTAKE_G_PER_BIRD_DAY = 22.0
WORM_SHARE = 0.30
PLANT_SHARE = 0.70
BUFFER_WEEKS = 2.0  # synergy SPEC default B_s
DAYS_PER_MONTH = 365.25 / 12.0


def genetics_keep(n0: float) -> float:
    """Birds that cannot be sold: synergy founders and the Ne floor, whichever is larger."""
    return float(genetics.keep_floor(n0, None, None, 3.0)["keep"])


def pounds_for_dollars(dollars: float, month: int) -> tuple[float, float]:
    price = float(engine.price_quote("quail", month)["F_prelim"])
    if price <= 0:
        raise RuntimeError("quail prepaid price must be positive")
    return dollars / price, price


def harvest_headcount(dollars: float, first: int = FIRST_MONTH, horizon: int = HORIZON) -> dict[int, float]:
    """Headcount removed at each month-end so that month's prepaid covers `dollars`."""
    model = engine.SPECIES["quail"]
    harvest: dict[int, float] = {}
    for month in range(first, horizon + 1):
        pounds, _price = pounds_for_dollars(dollars, month)
        week = engine.weeks_for_month(month) - 1
        harvest[week] = harvest.get(week, 0.0) + pounds * model.headcount_per_unit
    return harvest


def survives(n0: float, dollars: float, n_paths: int = engine.DEFAULT_PATHS, seed: int = engine.DEFAULT_SEED) -> bool:
    """True when the P10 tail still has the breeding flock after every monthly sale."""
    if n0 + 1e-9 < genetics_keep(1):
        return False
    model = engine.SPECIES["quail"]
    floor = genetics_keep(n0)
    weeks = engine.weeks_for_month(HORIZON)
    harvest = harvest_headcount(dollars)
    rate = engine._survival(n0, floor, weeks, harvest, model, n_paths, seed)
    return rate + 1e-12 >= engine.clear_fraction(engine.DEFAULT_QUANTILE)


def achievable_monthly_usd(n0: float, n_paths: int = engine.DEFAULT_PATHS, seed: int = engine.DEFAULT_SEED) -> float:
    """Largest constant monthly prepaid dollars from month 2 through the horizon."""
    if not survives(n0, 0.0, n_paths, seed):
        return 0.0
    lo = 0.0
    hi = TARGET_USD
    if survives(n0, hi, n_paths, seed):
        lo = hi
        for _ in range(8):
            nxt = hi * 2.0
            if not survives(n0, nxt, n_paths, seed):
                hi = nxt
                break
            lo = nxt
            hi = nxt
        else:
            return hi
    for _ in range(16):
        mid = 0.5 * (lo + hi)
        if survives(n0, mid, n_paths, seed):
            lo = mid
        else:
            hi = mid
    return lo


def required_n0(n_paths: int = engine.DEFAULT_PATHS, seed: int = engine.DEFAULT_SEED) -> dict:
    """Smallest starting flock that can hold $2,000 a month from month 2 on the P10 tail."""
    floor0 = genetics_keep(1)
    if survives(floor0, TARGET_USD, n_paths, seed):
        return {"n0": floor0, "feasible": True, "fail_closed": False}
    lo = floor0
    hi = floor0
    found = False
    while hi < N0_CAP:
        hi = min(N0_CAP, max(hi * 1.5, hi + 50.0))
        if survives(hi, TARGET_USD, n_paths, seed):
            found = True
            break
        lo = hi
        if hi >= N0_CAP:
            break
    if not found:
        return {
            "n0": None,
            "feasible": False,
            "fail_closed": True,
            "message": (
                "Stop. No starting flock inside the search cap can sell "
                f"${TARGET_USD:,.0f} a month from month {FIRST_MONTH} "
                "without using the breeding flock."
            ),
        }
    for _ in range(18):
        mid = 0.5 * (lo + hi)
        if survives(mid, TARGET_USD, n_paths, seed):
            hi = mid
        else:
            lo = mid
    return {"n0": float(math.ceil(hi - 1e-9)), "feasible": True, "fail_closed": False}


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(math.floor(q * (len(ordered) - 1)))
    idx = min(len(ordered) - 1, max(0, idx))
    return ordered[idx]


def herd_and_feed(n0: float, dollars: float, n_paths: int = engine.DEFAULT_PATHS, seed: int = engine.DEFAULT_SEED) -> dict:
    """Standing herd before each month's sale, and the worm and plant feed that herd requires."""
    model = engine.SPECIES["quail"]
    floor = genetics_keep(n0)
    weeks = engine.weeks_for_month(HORIZON)
    harvest = harvest_headcount(dollars)
    shocks = engine._shocks(model, weeks, n_paths, seed)
    capacity = engine._capacity(model, n0, floor)
    month_of_week = {}
    for month in range(1, HORIZON + 1):
        month_of_week[engine.weeks_for_month(month) - 1] = month
    standing = {month: [] for month in range(1, HORIZON + 1)}
    for row in shocks:
        n = float(n0)
        good = True
        for week, factor in enumerate(row):
            room = 1.0 - n / capacity
            if room < 0.0:
                room = 0.0
            n = n + n * (factor - 1.0) * room
            if good and week in month_of_week:
                standing[month_of_week[week]].append(n)
            take = harvest.get(week, 0.0)
            if take:
                n -= take
            if n < 0.0:
                n = 0.0
            if n + 1e-6 < floor:
                good = False
                break
    kg_per_bird = INTAKE_G_PER_BIRD_DAY * DAYS_PER_MONTH / 1000.0
    buffer_months = BUFFER_WEEKS / (52.0 / 12.0)
    rows = []
    for month in range(1, HORIZON + 1):
        light = _percentile(standing[month], engine.DEFAULT_QUANTILE)
        heavy = _percentile(standing[month], 1.0 - engine.DEFAULT_QUANTILE)
        worm = heavy * kg_per_bird * WORM_SHARE
        plant = heavy * kg_per_bird * PLANT_SHARE
        rows.append(
            {
                "month": month,
                "herd_p10": light,
                "herd_heavy": heavy,
                "worm_kg": worm,
                "plant_kg": plant,
                "buffer_worm_kg": worm * buffer_months,
                "buffer_plant_kg": plant * buffer_months,
                "sale_usd": TARGET_USD if month >= FIRST_MONTH else 0.0,
            }
        )
    steady = rows[-1]
    # A supply sized only to the light herd, with no buffer, is short of the heavy herd plus buffer.
    light_worm = steady["herd_p10"] * kg_per_bird * WORM_SHARE
    required_worm = steady["worm_kg"] + steady["buffer_worm_kg"]
    short = light_worm + 1e-9 < required_worm
    return {
        "floor": floor,
        "kg_per_bird_month": kg_per_bird,
        "months": rows,
        "steady_month": HORIZON,
        "steady_worm_kg": steady["worm_kg"],
        "steady_plant_kg": steady["plant_kg"],
        "steady_worm_t": steady["worm_kg"] / 1000.0,
        "steady_plant_t": steady["plant_kg"] / 1000.0,
        "feed_shortfall_fail_closed": short,
        "breeders_raided": False,
    }


def income_curve(n0_solved: float, n_paths: int = engine.DEFAULT_PATHS, seed: int = engine.DEFAULT_SEED) -> list[dict]:
    """N0 against the monthly dollars that N0 can hold from month 2."""
    floor0 = genetics_keep(1)
    hi = max(n0_solved * 1.8, floor0 * 4)
    anchors = [floor0]
    step = (hi - floor0) / 10.0
    for i in range(1, 11):
        anchors.append(floor0 + i * step)
    if n0_solved not in anchors:
        anchors.append(n0_solved)
    anchors = sorted(set(round(x, 1) for x in anchors))
    return [{"n0": n0, "monthly_usd": achievable_monthly_usd(n0, n_paths, seed)} for n0 in anchors]


def _svg_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _polyline(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def write_income_svg(curve: list[dict], n0: float, path: Path) -> None:
    width, height = 760, 460
    left, right, top, bottom = 70, 24, 36, 56
    xs = [row["n0"] for row in curve]
    ys = [row["monthly_usd"] for row in curve]
    xmin, xmax = min(xs), max(xs)
    ymax = max(max(ys), TARGET_USD) * 1.15
    ymin = 0.0

    def px(x: float) -> float:
        return left + (x - xmin) / (xmax - xmin) * (width - left - right)

    def py(y: float) -> float:
        return top + (1.0 - (y - ymin) / (ymax - ymin)) * (height - top - bottom)

    pts = [(px(row["n0"]), py(row["monthly_usd"])) for row in curve]
    step = 1000.0 if ymax <= 6000 else 2000.0
    ticks_y = [step * i for i in range(int(ymax // step) + 1)]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f7f4ee"/>',
        f'<text x="{left}" y="24" font-family="Georgia, serif" font-size="18" fill="#1c1915">Starting quail vs monthly meat dollars, P10</text>',
    ]
    for tick in ticks_y:
        y = py(tick)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="#e4dccf"/>')
        parts.append(f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" font-family="sans-serif" font-size="12" fill="#5c564c">{tick:,.0f}</text>')
    y_target = py(TARGET_USD)
    parts.append(
        f'<line x1="{left}" y1="{y_target:.1f}" x2="{width - right}" y2="{y_target:.1f}" stroke="#9a3412" stroke-dasharray="6 4"/>'
    )
    parts.append(
        f'<text x="{width - right}" y="{y_target - 6:.1f}" text-anchor="end" font-family="sans-serif" font-size="12" fill="#9a3412">$2,000 / month</text>'
    )
    parts.append(f'<polyline fill="none" stroke="#1d4e89" stroke-width="2.5" points="{_polyline(pts)}"/>')
    parts.append(f'<circle cx="{px(n0):.1f}" cy="{py(TARGET_USD):.1f}" r="5" fill="#9a3412"/>')
    parts.append(
        f'<text x="{px(n0) + 8:.1f}" y="{py(TARGET_USD) - 10:.1f}" font-family="sans-serif" font-size="13" fill="#9a3412">N0 {n0:,.0f}</text>'
    )
    parts.append(f'<line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" stroke="#1c1915"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" stroke="#1c1915"/>')
    parts.append(
        f'<text x="{(left + width - right) / 2:.0f}" y="{height - 16}" text-anchor="middle" font-family="sans-serif" font-size="13" fill="#1c1915">Starting birds N0</text>'
    )
    parts.append(
        f'<text x="18" y="{(top + height - bottom) / 2:.0f}" text-anchor="middle" font-family="sans-serif" font-size="13" fill="#1c1915" transform="rotate(-90 18 {(top + height - bottom) / 2:.0f})">Monthly prepaid dollars</text>'
    )
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_feed_svg(feed: dict, path: Path) -> None:
    rows = feed["months"]
    width, height = 780, 460
    left, right, top, bottom = 70, 64, 36, 56
    months = [row["month"] for row in rows]
    worm = [row["worm_kg"] for row in rows]
    plant = [row["plant_kg"] for row in rows]
    herd = [row["herd_heavy"] for row in rows]
    xmin, xmax = 1, HORIZON
    ymax = max(max(worm), max(plant)) * 1.2
    hmax = max(herd) * 1.05

    def px(month: float) -> float:
        return left + (month - xmin) / (xmax - xmin) * (width - left - right)

    def py(kg: float) -> float:
        return top + (1.0 - kg / ymax) * (height - top - bottom)

    def phy(birds: float) -> float:
        return top + (1.0 - birds / hmax) * (height - top - bottom)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f7f4ee"/>',
        f'<text x="{left}" y="24" font-family="Georgia, serif" font-size="18" fill="#1c1915">Feed for the heavy herd, with the meat sales on</text>',
    ]
    for frac in (0.25, 0.5, 0.75, 1.0):
        y = py(ymax * frac)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="#e4dccf"/>')
        parts.append(
            f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" font-family="sans-serif" font-size="12" fill="#5c564c">{ymax * frac:,.0f}</text>'
        )
    parts.append(
        f'<polyline fill="none" stroke="#3f6212" stroke-width="2.5" points="{_polyline([(px(m), py(v)) for m, v in zip(months, plant)])}"/>'
    )
    parts.append(
        f'<polyline fill="none" stroke="#9a3412" stroke-width="2.5" points="{_polyline([(px(m), py(v)) for m, v in zip(months, worm)])}"/>'
    )
    parts.append(
        f'<polyline fill="none" stroke="#1d4e89" stroke-width="2" stroke-dasharray="5 4" points="{_polyline([(px(m), phy(v)) for m, v in zip(months, herd)])}"/>'
    )
    parts.append(f'<line x1="{px(FIRST_MONTH):.1f}" y1="{top}" x2="{px(FIRST_MONTH):.1f}" y2="{height - bottom}" stroke="#5c564c" stroke-dasharray="3 3"/>')
    parts.append(
        f'<text x="{px(FIRST_MONTH) + 6:.1f}" y="{top + 16}" font-family="sans-serif" font-size="12" fill="#5c564c">first sale, month 2</text>'
    )
    parts.append(f'<line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" stroke="#1c1915"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" stroke="#1c1915"/>')
    parts.append(f'<line x1="{width - right}" y1="{top}" x2="{width - right}" y2="{height - bottom}" stroke="#1d4e89"/>')
    for frac in (0.0, 0.5, 1.0):
        birds = hmax * frac
        y = phy(birds)
        parts.append(
            f'<text x="{width - right + 6}" y="{y + 4:.1f}" font-family="sans-serif" font-size="11" fill="#1d4e89">{birds:,.0f}</text>'
        )
    parts.append(
        f'<text x="{(left + width - right) / 2:.0f}" y="{height - 16}" text-anchor="middle" font-family="sans-serif" font-size="13" fill="#1c1915">Month from purchase</text>'
    )
    parts.append(
        f'<text x="18" y="{(top + height - bottom) / 2:.0f}" text-anchor="middle" font-family="sans-serif" font-size="13" fill="#1c1915" transform="rotate(-90 18 {(top + height - bottom) / 2:.0f})">Feed kg / month</text>'
    )
    legend_y = height - bottom - 18
    parts.append(f'<line x1="{left + 8}" y1="{legend_y}" x2="{left + 28}" y2="{legend_y}" stroke="#3f6212" stroke-width="2.5"/>')
    parts.append(f'<text x="{left + 34}" y="{legend_y + 4}" font-family="sans-serif" font-size="12" fill="#1c1915">Plant</text>')
    parts.append(f'<line x1="{left + 90}" y1="{legend_y}" x2="{left + 110}" y2="{legend_y}" stroke="#9a3412" stroke-width="2.5"/>')
    parts.append(f'<text x="{left + 116}" y="{legend_y + 4}" font-family="sans-serif" font-size="12" fill="#1c1915">Worms</text>')
    parts.append(f'<line x1="{left + 180}" y1="{legend_y}" x2="{left + 200}" y2="{legend_y}" stroke="#1d4e89" stroke-width="2" stroke-dasharray="5 4"/>')
    parts.append(f'<text x="{left + 206}" y="{legend_y + 4}" font-family="sans-serif" font-size="12" fill="#1c1915">Heavy herd (right scale)</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_pngs(curve: list[dict], n0: float, feed: dict, out_dir: Path) -> list[Path]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return []
    income = out_dir / "quail_income_n0.png"
    feed_path = out_dir / "quail_income_feed.png"
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    ax.plot([row["n0"] for row in curve], [row["monthly_usd"] for row in curve], color="#1d4e89", lw=2.2)
    ax.axhline(TARGET_USD, color="#9a3412", ls="--", lw=1.2, label="$2,000 / month")
    ax.scatter([n0], [TARGET_USD], color="#9a3412", zorder=3)
    ax.annotate(f"N0 {n0:,.0f}", (n0, TARGET_USD), textcoords="offset points", xytext=(8, 8), color="#9a3412")
    ax.set_xlabel("Starting birds N0")
    ax.set_ylabel("Monthly prepaid dollars")
    ax.set_title("Starting quail vs monthly meat dollars, P10")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(income, dpi=140)
    plt.close(fig)

    rows = feed["months"]
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    ax.plot([row["month"] for row in rows], [row["plant_kg"] for row in rows], color="#3f6212", lw=2.2, label="Plant kg/mo")
    ax.plot([row["month"] for row in rows], [row["worm_kg"] for row in rows], color="#9a3412", lw=2.2, label="Worm kg/mo")
    ax.axvline(FIRST_MONTH, color="#5c564c", ls=":", lw=1)
    ax.set_xlabel("Month from purchase")
    ax.set_ylabel("Feed kg / month")
    ax2 = ax.twinx()
    ax2.plot([row["month"] for row in rows], [row["herd_heavy"] for row in rows], color="#1d4e89", lw=1.6, ls="--", label="Heavy herd")
    ax2.set_ylabel("Heavy herd, birds", color="#1d4e89")
    ax.set_title("Feed for the heavy herd, sales from month 2")
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(feed_path, dpi=140)
    plt.close(fig)
    return [income, feed_path]


def smoke(path: Path | None = None) -> dict:
    solved = required_n0()
    assert solved["feasible"] and solved["n0"] is not None
    n0 = float(solved["n0"])
    assert n0 + 1e-6 >= genetics_keep(1)
    assert survives(n0, TARGET_USD)
    assert not survives(max(genetics_keep(1), n0 * 0.90), TARGET_USD)
    pounds2, price2 = pounds_for_dollars(TARGET_USD, FIRST_MONTH)
    pounds_h, price_h = pounds_for_dollars(TARGET_USD, HORIZON)
    harvest = harvest_headcount(TARGET_USD)
    month1_week = engine.weeks_for_month(1) - 1
    assert month1_week not in harvest
    feed = herd_and_feed(n0, TARGET_USD)
    assert feed["feed_shortfall_fail_closed"]
    assert feed["breeders_raided"] is False
    assert feed["steady_worm_kg"] > 0 and feed["steady_plant_kg"] > feed["steady_worm_kg"]
    curve = income_curve(n0)
    below = [row for row in curve if row["n0"] + 1 < n0]
    above = [row for row in curve if row["n0"] > n0 + 1]
    assert below and max(row["monthly_usd"] for row in below) < TARGET_USD - 1
    assert above and max(row["monthly_usd"] for row in above) > TARGET_USD + 200
    out_dir = Path(__file__).resolve().parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    income_svg = out_dir / "quail_income_n0.svg"
    feed_svg = out_dir / "quail_income_feed.svg"
    write_income_svg(curve, n0, income_svg)
    write_feed_svg(feed, feed_svg)
    pngs = write_pngs(curve, n0, feed, out_dir)
    payload = {
        "ok": True,
        "stage": "Stage 4 quail planning. Not a purchase. Stage 1 worms remain the only spend.",
        "growth_tag": "ASSUMPTION",
        "feed_tag": "ASSUMPTION",
        "quantile": engine.DEFAULT_QUANTILE,
        "target_usd_per_month": TARGET_USD,
        "first_sale_month": FIRST_MONTH,
        "horizon_month": HORIZON,
        "n0": n0,
        "genetics_floor": genetics_keep(1),
        "breed_floor_at_n0": feed["floor"],
        "f_prelim_month_2": price2,
        "lb_per_month_at_2": pounds2,
        "f_prelim_month_horizon": price_h,
        "lb_per_month_at_horizon": pounds_h,
        "steady_worm_kg": feed["steady_worm_kg"],
        "steady_plant_kg": feed["steady_plant_kg"],
        "steady_worm_t": feed["steady_worm_t"],
        "steady_plant_t": feed["steady_plant_t"],
        "intake_g_per_bird_day": INTAKE_G_PER_BIRD_DAY,
        "worm_share": WORM_SHARE,
        "plant_share": PLANT_SHARE,
        "buffer_weeks": BUFFER_WEEKS,
        "feed_shortfall_fail_closed": True,
        "curve": curve,
        "feed_months": feed["months"],
        "plots": [str(income_svg), str(feed_svg), *[str(item) for item in pngs]],
    }
    out = path or out_dir / "quail_income_smoke.json"
    slim = {key: value for key, value in payload.items() if key not in ("curve", "feed_months")}
    slim["curve_n0"] = [row["n0"] for row in curve]
    slim["curve_usd"] = [row["monthly_usd"] for row in curve]
    out.write_text(json.dumps(slim, indent=2) + "\n", encoding="utf-8")
    payload["smoke_path"] = str(out)
    return payload


if __name__ == "__main__":
    result = smoke()
    print(f"N0={result['n0']:.1f}")
    print(
        f"lb/mo at month 2={result['lb_per_month_at_2']:.2f} at F_prelim ${result['f_prelim_month_2']:.4f}; "
        f"month {result['horizon_month']}={result['lb_per_month_at_horizon']:.2f} lb "
        f"at ${result['f_prelim_month_horizon']:.4f}"
    )
    print(
        f"steady feed month {result['horizon_month']}: "
        f"worms {result['steady_worm_kg']:.1f} kg/mo ({result['steady_worm_t']:.3f} t), "
        f"plants {result['steady_plant_kg']:.1f} kg/mo ({result['steady_plant_t']:.3f} t)"
    )
    print("fail_closed_on_feed_shortfall", result["feed_shortfall_fail_closed"])
    for plot in result["plots"]:
        print(plot)
