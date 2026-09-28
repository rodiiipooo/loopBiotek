#!/usr/bin/env python3
"""Decision charts for the planning models. Regenerates the PNG gallery.

Needs matplotlib (plotting only). The ops screen itself stays on the
standard library and only serves the pictures this script writes.

Stage 1 worms remain the only spend. Quail charts are Stage 4 planning.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "plots"
OPS = ROOT / "ops-dashboard"
GENETICS = ROOT / "genetics"
for folder in (OPS, GENETICS):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import delivery  # noqa: E402
import engine  # noqa: E402
import quail_income  # noqa: E402
import reproduction as genetics  # noqa: E402

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError as err:
    raise SystemExit(
        "matplotlib is required to regenerate these charts. "
        "The ops screen does not need it. Install with: python3 -m pip install matplotlib"
    ) from err


def _finish(fig, path: Path, note: str, after_layout=None) -> None:
    lines = note.count("\n") + 1
    if lines == 1:
        fig.text(0.01, 0.005, note, fontsize=8, color="#5c564c")
        fig.tight_layout(rect=(0, 0.07, 1, 1))
    else:
        bottom = 0.02 + 0.028 * lines
        fig.text(0.01, 0.01, note, fontsize=8, color="#5c564c", va="bottom", linespacing=1.35)
        fig.tight_layout(rect=(0, bottom, 1, 1))
    if after_layout is not None:
        after_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)


def birds_vs_month(order_lb: float = 40.0) -> dict:
    """P10 starters for one order, plus locked prepaid F_prelim at the same month.

    The herd series stay on the upper panel. F_prelim is a companion panel so a
    third unit ($/lb) does not sit on top of birds per pound and N0.
    """
    months = [1, 2, 3, 4, 6, 8, 10, 12, 15, 18]
    rows = [delivery.n0_required(order_lb, month, "quail", engine.DEFAULT_QUANTILE) for month in months]
    quotes = [engine.price_quote("quail", month) for month in months]
    birds = [row["birds_per_lb"] for row in rows]
    herds = [row["n0"] for row in rows]
    f_prelim = [float(quote["F_prelim"]) for quote in quotes]
    p0 = float(quotes[0]["E_P0"])
    spot_prepaid = float(engine.FAIRNESS) * p0
    fig, (ax, axp) = plt.subplots(
        2,
        1,
        figsize=(8.8, 8.1),
        sharex=True,
        gridspec_kw={"height_ratios": [1.45, 1.0]},
    )
    ax.plot(months, birds, color="#1d4e89", lw=2.2, marker="o", label="Birds per lb")
    ax.set_ylabel("Starters per delivered pound")
    ax2 = ax.twinx()
    ax2.plot(months, herds, color="#9a3412", lw=2.2, marker="s", label="Starting herd N0")
    ax2.set_ylabel("Starting herd for this order", color="#9a3412")
    ax2.tick_params(axis="y", colors="#9a3412")
    ax.set_title(f"P10 starters for a {order_lb:.0f} lb quail order")
    ax.axvline(6, color="#8a5a12", ls=":", lw=1.15, zorder=0, label="Month 6")
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, frameon=False, loc="upper right")

    axp.plot(months, f_prelim, color="#3f6212", lw=2.2, marker="D", label="F_prelim")
    axp.axhline(
        spot_prepaid,
        color="#5c564c",
        ls="--",
        lw=1.15,
        label="0.9 × spot (prepaid at T = 0)",
    )
    axp.axvline(6, color="#8a5a12", ls=":", lw=1.15, zorder=0)
    # Invisible herd ticks keep the same right gutter so the months line up.
    axp_right = axp.twinx()
    axp_right.set_ylim(ax2.get_ylim())
    axp_right.set_yticks(ax2.get_yticks())
    axp_right.set_ylabel("Starting herd for this order", color="#ffffff")
    axp_right.tick_params(axis="y", colors="#ffffff", length=0)
    axp.set_xlabel("Delivery month T")
    axp.set_ylabel("Prepaid F_prelim ($/lb)")
    axp.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _pos: f"{value:.2f}"))
    low = min(f_prelim)
    high = max(spot_prepaid, max(f_prelim))
    axp.set_ylim(low - 0.32, high + 0.1)
    axp.legend(frameon=False, loc="lower left")

    def _align_panels() -> None:
        box = ax.get_position()
        for host in (axp, axp_right):
            old = host.get_position()
            host.set_position([box.x0, old.y0, box.width, old.height])

    _finish(
        fig,
        OUT / "birds_per_lb_vs_month.png",
        "ASSUMPTION growth (26-week doubling). Floor of 68 is the Ne formula. P10.\n"
        "F_prelim = 0.9 * E[P0] * ((1+0.027)/(1+0.0424))^(month/12). 3-month T-bill yield.\n"
        "Stage 4 planning. Not a purchase. Around month 6: ~2.5 starters/lb, N0 ~100,\n"
        "and F_prelim is still near 0.9 x spot. A shorter T burns starters.\n"
        "A much later T trims starters only a little and discounts the prepaid.",
        after_layout=_align_panels,
    )
    return {
        "months": months,
        "birds_per_lb": birds,
        "n0": herds,
        "f_prelim": f_prelim,
        "p0": p0,
        "spot_prepaid_t0": spot_prepaid,
        "r_inf": engine.R_INF,
        "r_tbill": engine.R_TBILL,
        "fairness": engine.FAIRNESS,
    }


def split_vs_soon() -> dict:
    orders = [
        {"qty_lb": 15, "earliest_month": 3, "latest_month": 3},
        {"qty_lb": 15, "earliest_month": 3, "latest_month": 12},
    ]
    rec = delivery.recommend(orders, "quail", engine.DEFAULT_QUANTILE)
    soon = rec["all_soon"]
    best = rec["recommended"]
    labels = ["All 30 lb\nin month 3", "15 lb in month 3\n+ 15 lb in month 12"]
    values = [soon["n0"], best["n0"]]
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    bars = ax.bar(labels, values, color=["#9a3412", "#1d4e89"], width=0.55)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 4, f"{value:.0f} birds", ha="center", va="bottom")
    ax.set_ylabel("Starting herd N0")
    ax.set_title("Same 30 lb book: ship it all soon, or split")
    ax.set_ylim(0, max(values) * 1.2)
    _finish(
        fig,
        OUT / "delivery_split_vs_soon.png",
        "ASSUMPTION growth. Genetics floor still applies. P10. The later lot is allowed to wait until month 12. Stage 4 planning.",
    )
    return {"all_soon_n0": soon["n0"], "split_n0": best["n0"], "split_lots": best["lots"]}


def ne_vs_sale() -> dict:
    """Sell a 40 male / 120 female flock in the 1:3 ratio until Ne falls through 50."""
    sold = []
    ne = []
    remaining = []
    allowed = []
    for k in range(0, 31):
        plan = genetics.cull_plan(40, 120, k, 3 * k, n0=20, females_per_male=3.0)
        sold.append(k + 3 * k)
        ne.append(plan["Ne_after"])
        remaining.append(plan["males_after"] + plan["females_after"])
        allowed.append(plan["allowed"])
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    ax.plot(sold, ne, color="#1d4e89", lw=2.2, label="Ne after the sale")
    ax.axhline(50, color="#9a3412", ls="--", label="Ne = 50")
    refuse_x = [x for x, ok in zip(sold, allowed) if not ok]
    if refuse_x:
        ax.axvspan(min(refuse_x), max(sold), color="#fde8e4", zorder=0, label="Refused")
    ax.set_xlabel("Birds sold (1 male : 3 females kept in the ratio)")
    ax.set_ylabel("Effective population Ne")
    ax.set_title("Quail sale versus the Ne = 50 floor")
    ax.legend(frameon=False, loc="upper right")
    _finish(
        fig,
        OUT / "ne_vs_sale.png",
        "Wright Ne is a formula. Quail ratio 1:3. Refuse when Ne would drop below 50 (17 males and 51 females). Not a growth simulation.",
    )
    return {"sold": sold, "ne": ne, "remaining": remaining, "allowed": allowed}


def leakage_plot() -> dict:
    xs = [i / 20 for i in range(21)]
    hatch, fertility, viability, egg, reject = [], [], [], [], []
    for x in xs:
        row = genetics.leakage("quail", x_inbred=x)
        hatch.append(row["hatch"])
        fertility.append(row["fecundity_index"])
        viability.append(row["growth_index"])
        egg.append(row["egg_rate_index"])
        reject.append(row["reject_rate"])
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    pct = [100 * x for x in xs]
    ax.plot(pct, hatch, color="#1d4e89", lw=2.2, label="Hatch (Sato)")
    ax.plot(pct, fertility, color="#3f6212", lw=2.0, label="Fertility index (Sato)")
    ax.plot(pct, viability, color="#9a3412", lw=2.0, label="Viability index (Sato)")
    ax.plot(pct, egg, color="#8a5a12", lw=1.6, ls="--", label="Egg-rate index (other study)")
    ax.plot(pct, reject, color="#5c564c", lw=1.6, ls=":", label="Added reject (assumption)")
    ax.set_xlabel("Percent of offspring that are full sibs")
    ax.set_ylabel("Trait after the haircut")
    ax.set_title("Quail inbreeding leakage")
    ax.set_ylim(0, 1.05)
    ax.legend(frameon=False, loc="center left")
    _finish(
        fig,
        OUT / "quail_inbreeding_leakage.png",
        "SOURCED: Sato slopes for hatch, fertility, viability. Egg rate is a different incross study. Reject rate is ASSUMPTION. Stage 4 planning.",
    )
    return {"x": xs, "hatch": hatch, "reject": reject}


def worm_sell_room() -> dict:
    herds = [4000, 8000, 12000, 16500, 24000, 33000]
    by_herd = []
    for n0 in herds:
        limit = engine.sell_limit("worms", n0, [], reliability=engine.DEFAULT_QUANTILE, horizon_months=12)
        by_herd.append(limit["safe_to_sell_units"])
    months = [3, 6, 9, 12, 18, 24]
    by_month = []
    for month in months:
        limit = engine.sell_limit("worms", 16500, [], reliability=engine.DEFAULT_QUANTILE, horizon_months=month)
        by_month.append(limit["safe_to_sell_units"])
    fig, axes = plt.subplots(1, 2, figsize=(8.8, 4.6))
    axes[0].plot(herds, by_herd, color="#1d4e89", lw=2.2, marker="o")
    axes[0].set_xlabel("Starting worms N0")
    axes[0].set_ylabel("P10 sell room, lb")
    axes[0].set_title("At month 12")
    axes[1].plot(months, by_month, color="#9a3412", lw=2.2, marker="o")
    axes[1].set_xlabel("Delivery month")
    axes[1].set_ylabel("P10 sell room, lb")
    axes[1].set_title("N0 = 16,500")
    fig.suptitle("Worm safe-to-sell on the P10 tail", fontsize=13)
    _finish(
        fig,
        OUT / "worm_p10_sell_room.png",
        "ASSUMPTION worm growth (13-week doubling). Not worm_growth_mc. P10. Stage 1 screen. Not a purchase.",
    )
    return {"n0": herds, "lb_at_month_12": by_herd, "months": months, "lb_at_16500": by_month}


def copy_income_plots() -> dict:
    result = quail_income.smoke()
    src = OPS / "results"
    for name, dest in (
        ("quail_income_n0.png", "quail_n0_for_2000.png"),
        ("quail_income_feed.png", "quail_feed_vs_herd.png"),
    ):
        shutil.copyfile(src / name, OUT / dest)
    return {"n0": result["n0"], "lb_month_2": result["lb_per_month_at_2"], "worm_kg": result["steady_worm_kg"], "plant_kg": result["steady_plant_kg"]}


def main() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    birds = birds_vs_month()
    assert birds["birds_per_lb"][0] > birds["birds_per_lb"][-1]
    assert birds["n0"][0] > birds["n0"][-1]
    assert birds["f_prelim"][0] > birds["f_prelim"][-1]
    at_six = birds["months"].index(6)
    assert abs(birds["birds_per_lb"][at_six] - 2.45) < 0.15
    assert 90 < birds["n0"][at_six] < 110
    spot_prepaid = birds["fairness"] * birds["p0"]
    assert abs(birds["f_prelim"][at_six] / spot_prepaid - 1.0) < 0.03
    for month, quoted in zip(birds["months"], birds["f_prelim"]):
        years = month / 12.0
        expected = (
            birds["fairness"]
            * birds["p0"]
            * ((1.0 + birds["r_inf"]) / (1.0 + birds["r_tbill"])) ** years
        )
        assert abs(quoted - expected) < 1e-9
    split = split_vs_soon()
    assert split["split_n0"] + 1 < split["all_soon_n0"]
    assert any(lot["month"] > 3 for lot in split["split_lots"])
    ne = ne_vs_sale()
    assert ne["ne"][0] > 50 and ne["ne"][-1] < 50
    assert any(ok for ok in ne["allowed"]) and any(not ok for ok in ne["allowed"])
    leak = leakage_plot()
    assert abs(leak["hatch"][0] - 0.75) < 1e-9
    # 40% full-sib offspring -> F_bar = 0.10, hatch 0.6902
    mid = leak["hatch"][8]
    assert abs(mid - 0.6902) < 1e-3
    income = copy_income_plots()
    assert income["n0"] >= 68
    worms = worm_sell_room()
    assert worms["lb_at_month_12"][0] < worms["lb_at_month_12"][-1]
    assert worms["lb_at_16500"][0] < worms["lb_at_16500"][-1]
    teachings = {
        "birds_per_lb_vs_month.png": "Around month 6 a 40 lb P10 order needs about 2.5 starters per pound (N0 about 100) while F_prelim is still near 0.9 times spot. A shorter month burns starters. A much later month trims starters only a little and discounts the prepaid.",
        "delivery_split_vs_soon.png": "A book that can wait for part of the pounds needs fewer starters than shipping all of it in month 3.",
        "ne_vs_sale.png": "A quail sale that would leave Ne under 50 is refused.",
        "quail_inbreeding_leakage.png": "More full-sib offspring lowers hatch and viability on the Sato slopes.",
        "quail_n0_for_2000.png": "About 2,816 starters hold $2,000 a month from month 2 on the P10 tail.",
        "quail_feed_vs_herd.png": "Worm and plant feed rise with the heavy herd; a short ration fails closed.",
        "worm_p10_sell_room.png": "Worm P10 room grows with the starting herd and with a later month.",
    }
    for name in teachings:
        file = OUT / name
        assert file.is_file() and file.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    payload = {
        "ok": True,
        "teachings": teachings,
        "birds": birds,
        "split": {"all_soon_n0": split["all_soon_n0"], "split_n0": split["split_n0"]},
        "income_n0": income["n0"],
        "worm_lb_at_16500_month_12": worms["lb_at_month_12"][worms["n0"].index(16500)],
    }
    (OUT / "decision_plots_smoke.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = main()
    print("plots in", OUT)
    for name, line in result["teachings"].items():
        print(f"{name}: {line}")
