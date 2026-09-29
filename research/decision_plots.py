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
QUAIL = ROOT / "quail"
for folder in (OPS, GENETICS, QUAIL):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import delivery  # noqa: E402
import engine  # noqa: E402
import quail_income  # noqa: E402
import quail_model  # noqa: E402
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
    """Flock on hand today for one dressed order, plus F_prelim at that week.

    Upper panel: N_today, stacked as males and females at 1:3. Lower panel:
    prepaid $/lb, so the price scale does not cover the flock.
    """
    months = [1, 2, 3, 4, 6, 8, 10, 12, 15, 18]
    weeks = [engine.weeks_for_month(month) for month in months]
    # This panel is the meat order without the layer-replacement pipeline.
    # peak_cull_layers.png is the with-versus-without comparison.
    rows = [delivery.flock_today(week, order_lb, sustain_peak=False) for week in weeks]
    if not all(row["fail_closed"] for row in rows):
        raise RuntimeError("flock_today would raid the breed floor")
    totals = [row["n_today"] for row in rows]
    males = [row["males"] for row in rows]
    females = [row["females"] for row in rows]
    f_prelim = [row["f_prelim"] for row in rows]
    p0 = rows[0]["p0"]
    spot_prepaid = float(engine.FAIRNESS) * p0
    knee = months.index(6)
    fig, (ax, axp) = plt.subplots(
        2,
        1,
        figsize=(8.8, 8.2),
        sharex=True,
        gridspec_kw={"height_ratios": [1.5, 1.0]},
    )
    ax.stackplot(
        weeks,
        males,
        females,
        colors=["#c4a484", "#1d4e89"],
        labels=["Males today", "Females today"],
        alpha=0.9,
    )
    ax.plot(weeks, totals, color="#1c1915", lw=1.6, marker="o", label="N_today")
    ax.axvline(weeks[knee], color="#8a5a12", ls=":", lw=1.15, zorder=0)
    ax.set_ylabel("Birds on hand today")
    ax.set_title(f"Flock today for a {order_lb:.0f} lb quail delivery from surplus")
    ax.legend(frameon=False, loc="upper right")
    knee_row = rows[knee]
    ax.annotate(
        f"x = {order_lb:.0f} lb\nweek {knee_row['week']}\n{knee_row['males']}♂ {knee_row['females']}♀",
        xy=(knee_row["week"], knee_row["n_today"]),
        xytext=(knee_row["week"] + 14, max(totals) * 0.42),
        fontsize=8,
        color="#1c1915",
        arrowprops={"arrowstyle": "->", "color": "#8a5a12", "lw": 0.8},
    )

    axp.plot(weeks, f_prelim, color="#3f6212", lw=2.2, marker="D", label="F_prelim")
    axp.axhline(spot_prepaid, color="#5c564c", ls="--", lw=1.15, label="0.9 × spot (T = 0)")
    axp.axvline(weeks[knee], color="#8a5a12", ls=":", lw=1.15, zorder=0)
    axp.set_xlabel("Delivery week n")
    axp.set_ylabel("Prepaid F_prelim ($/lb)")
    axp.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _pos: f"{value:.2f}"))
    low = min(f_prelim)
    high = max(spot_prepaid, max(f_prelim))
    pad = max(0.05, (high - low) * 0.8)
    axp.set_ylim(low - pad, high + pad * 0.35)
    axp.legend(frameon=False, loc="lower left")
    _finish(
        fig,
        OUT / "birds_per_lb_vs_month.png",
        f"Order x = {order_lb:.0f} lb dressed. N_today sells surplus only and leaves a 1♂:3♀ flock.\n"
        "P10 herd for x * 1.15 / 0.9, or the Ne nucleus plus the mortality pipeline, whichever is larger.\n"
        "F_prelim = 0.9 * E[P0] * ((1+0.027)/(1+0.0401))^(week/52). FRED DTB3 4.01% (2026-09-22).\n"
        "Week 26 (~6 mo) is the knee: a short lead needs a much larger flock; a long lead\n"
        "adds mortality to the pipeline and discounts the prepaid. This panel leaves hens\n"
        "in peak forever. The replacement pipeline is on peak_cull_layers.png. Stage 4 planning.",
    )
    return {
        "order_lb": order_lb,
        "months": months,
        "weeks": weeks,
        "n_today": totals,
        "males": males,
        "females": females,
        "binding": [row["binding"] for row in rows],
        "fail_closed": [row["fail_closed"] for row in rows],
        "f_prelim": f_prelim,
        "p0": p0,
        "spot_prepaid_t0": spot_prepaid,
        "r_inf": engine.R_INF,
        "r_tbill": engine.R_TBILL,
        "fairness": engine.FAIRNESS,
        "knee": knee_row,
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


def peak_cull_chart() -> dict:
    """Productive fraction by age, and the $10k / 1-year flock with and without replacement."""
    table = quail_model.productive_fraction_table(60)
    weeks = [row["age_weeks"] for row in table]
    fraction = [row["productive_fraction"] for row in table]
    comp = delivery.cascade_growth_today()
    if not comp["fail_closed"]:
        raise RuntimeError("peak-cull flock would raid the breed floor")
    fig, (ax, axb) = plt.subplots(1, 2, figsize=(10.4, 4.9))
    ax.plot(weeks, fraction, color="#1d4e89", lw=2.2, label="Productive fraction")
    ax.axhline(quail_model.PEAK_SLOT_MIN, color="#9a3412", ls="--", lw=1.1, label="Slot gate 0.85")
    peak_weeks = [week for week, row in zip(weeks, table) if row["in_peak"]]
    if peak_weeks:
        ax.axvspan(min(peak_weeks), max(peak_weeks), color="#e7f0e4", zorder=0, label="In peak")
    ax.axvline(26, color="#8a5a12", ls=":", lw=1.1)
    ax.set_xlim(0, 60)
    ax.set_ylim(-0.02, 1.08)
    ax.set_xlabel("Age (weeks)")
    ax.set_ylabel("Fraction of peak hen-day")
    ax.set_title("When a hen is still in peak lay")
    ax.legend(frameon=False, loc="upper right", fontsize=8)

    labels = ["Without\npeak cull", "With peak-cull\nreplacement"]
    values = [comp["n_today_immortal"], comp["n_today"]]
    bars = axb.bar(labels, values, color=["#c4a484", "#1d4e89"], width=0.62)
    for bar, value in zip(bars, values):
        axb.text(
            bar.get_x() + bar.get_width() / 2,
            value + max(values) * 0.015,
            f"{value:,.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    added = comp["n_today"] - comp["n_today_immortal"]
    axb.annotate(
        f"+{added:,.0f} birds in the pullet pipeline\n"
        f"{comp['hens_into_cage_per_week']:.2f} hens/week into the cage",
        xy=(1, comp["n_today"]),
        xytext=(0.15, comp["n_today"] - max(values) * 0.22),
        fontsize=8,
        color="#1c1915",
        arrowprops={"arrowstyle": "->", "color": "#1d4e89", "lw": 0.8},
    )
    axb.set_ylabel("Birds on hand today")
    axb.set_title(f"${comp['dollars'] / 1000:.0f}k prepaid at week {comp['week']}")
    axb.set_ylim(0, max(values) * 1.18)
    _finish(
        fig,
        OUT / "peak_cull_layers.png",
        "Left: straight lines between sourced anchors (onset week 6, peak rate week 15, sharp drop after week 26).\n"
        "The slot gate 0.85 is an assumption. It keeps weeks 14–33, about 6 months of lay after week 8.\n"
        f"Right: ${comp['dollars']:,.0f} of surplus meat at week {comp['week']} is {comp['order_lb']:.0f} lb "
        f"at F_prelim ${comp['f_prelim']:.2f}/lb.\n"
        "The added birds are the pullet pipeline for 51 peak hen slots at 1 male : 3 females. Spent hens are not the order.\n"
        "Breeders are not sold. Stage 4 planning. Not a purchase.",
    )
    return {
        "n_today": comp["n_today"],
        "n_today_immortal": comp["n_today_immortal"],
        "order_lb": comp["order_lb"],
        "f_prelim": comp["f_prelim"],
        "pipeline_birds": comp["pipeline_birds"],
        "hens_into_cage_per_week": comp["hens_into_cage_per_week"],
        "fraction_at_15": fraction[15],
        "fraction_at_34": fraction[34],
        "fail_closed": comp["fail_closed"],
    }


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
    assert all(birds["fail_closed"])
    assert all(f == 3 * m for m, f in zip(birds["males"], birds["females"]))
    assert birds["n_today"][0] > birds["n_today"][birds["months"].index(6)]
    knee_i = birds["months"].index(6)
    assert birds["weeks"][knee_i] == 26
    assert min(birds["n_today"]) == min(birds["n_today"][2:6])
    bigger = delivery.flock_today(26, 80.0, sustain_peak=False)
    assert bigger["n_today"] > birds["knee"]["n_today"]
    assert bigger["fail_closed"] and bigger["females"] == 3 * bigger["males"]
    assert abs(birds["r_tbill"] - 0.0401) < 1e-12
    spot_prepaid = birds["fairness"] * birds["p0"]
    assert abs(birds["f_prelim"][knee_i] / spot_prepaid - 1.0) < 0.03
    for week, quoted in zip(birds["weeks"], birds["f_prelim"]):
        years = week / 52.0
        expected = (
            birds["fairness"]
            * birds["p0"]
            * ((1.0 + birds["r_inf"]) / (1.0 + birds["r_tbill"])) ** years
        )
        assert abs(quoted - expected) < 1e-6
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
    peak = peak_cull_chart()
    assert peak["fail_closed"]
    assert peak["n_today"] > peak["n_today_immortal"]
    assert abs(peak["fraction_at_15"] - 1.0) < 1e-12
    assert peak["fraction_at_34"] < 0.85
    income = copy_income_plots()
    assert income["n0"] >= 68
    worms = worm_sell_room()
    assert worms["lb_at_month_12"][0] < worms["lb_at_month_12"][-1]
    assert worms["lb_at_16500"][0] < worms["lb_at_16500"][-1]
    teachings = {
        "birds_per_lb_vs_month.png": "For 40 lb at week n, N_today is the 1:3 flock on hand now that can sell surplus only. The low point is near week 26. F_prelim uses the 4.01% 3-month bill.",
        "delivery_split_vs_soon.png": "A book that can wait for part of the pounds needs fewer starters than shipping all of it in month 3.",
        "ne_vs_sale.png": "A quail sale that would leave Ne under 50 is refused.",
        "quail_inbreeding_leakage.png": "More full-sib offspring lowers hatch and viability on the Sato slopes.",
        "quail_n0_for_2000.png": f"About {income['n0']:,.0f} starters hold $2,000 a month from month 2 on the P10 tail.",
        "quail_feed_vs_herd.png": "Worm and plant feed rise with the heavy herd; a short ration fails closed.",
        "worm_p10_sell_room.png": "Worm P10 room grows with the starting herd and with a later month.",
        "peak_cull_layers.png": (
            f"$10k at week 52 needs {peak['n_today']:,.0f} birds with the peak-cull pipeline "
            f"and {peak['n_today_immortal']:,.0f} without it. Hens leave the peak slot after week 33."
        ),
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
        "peak_cull": {
            "n_today": peak["n_today"],
            "n_today_immortal": peak["n_today_immortal"],
            "order_lb": peak["order_lb"],
            "pipeline_birds": peak["pipeline_birds"],
        },
        "worm_lb_at_16500_month_12": worms["lb_at_month_12"][worms["n0"].index(16500)],
    }
    (OUT / "decision_plots_smoke.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = main()
    print("plots in", OUT)
    for name, line in result["teachings"].items():
        print(f"{name}: {line}")
