#!/usr/bin/env python3
"""Figures for the cascade growth graph. Planning pictures, not a purchase.

Stage 1 worms remain the only spend. Matplotlib is used only here.
"""

from __future__ import annotations

from pathlib import Path

import model

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
except ImportError as err:
    raise SystemExit(
        "matplotlib is required for these figures. "
        "Install with: python3 -m pip install matplotlib"
    ) from err


PLOTS = Path(__file__).resolve().parents[1] / "plots"
PRACTICE = "#1d4e89"
MALE_HEAVY = "#9a3412"
INK = "#1c1915"
MUTED = "#5c564c"

KIND_COLOR = {
    "fecundity": "#1d4e89",
    "maturation": "#44403c",
    "feed": "#9a3412",
    "manure": "#a16207",
    "nutrient": "#3f6212",
    "competition": "#7c3aed",
}


def _finish(fig, path: Path, note: str) -> None:
    lines = note.count("\n") + 1
    bottom = 0.012 + 0.022 * lines
    fig.text(0.01, 0.008, note, fontsize=8, color=MUTED, va="bottom", linespacing=1.35)
    fig.tight_layout(rect=(0, bottom, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _edge_weights(practice: dict) -> dict[tuple[str, str], float]:
    """Mean of the practice median flow, weeks 20–40, keyed by graph edge."""
    weeks = practice["weeks"]
    start = weeks.index(20) if 20 in weeks else 0
    stop = weeks.index(40) if 40 in weeks else len(weeks) - 1

    def mean(name: str) -> float:
        if name not in practice["series"]:
            return 0.0
        chunk = practice["series"][name]["p50"][start : stop + 1]
        return sum(chunk) / len(chunk) if chunk else 0.0

    castings = mean("castings_kg")
    return {
        ("quail.breeder_f", "worms.breeder"): mean("manure_to_worms_kg"),
        ("greens.canopy", "quail.breeder_f"): mean("greens_to_quail_kg"),
        ("greens.canopy", "crickets.nymph"): mean("greens_to_crickets_kg"),
        ("greens.canopy", "isopods.juvenile"): mean("greens_to_isopods_kg"),
        ("crickets.adult", "quail.breeder_f"): mean("crickets_to_quail_kg"),
        ("crickets.adult", "fish.growout"): mean("crickets_to_fish_kg"),
        ("worms.juvenile", "quail.breeder_f"): mean("worms_to_quail_kg"),
        ("worms.juvenile", "fish.growout"): mean("worms_to_fish_kg"),
        ("algae.culture", "fish.growout"): mean("algae_to_fish_kg"),
        ("isopods.adult", "worms.breeder"): mean("isopod_manure_kg"),
        ("worms.breeder", "greens.canopy"): castings * model.CASTINGS_TO_GREENS,
        ("worms.breeder", "algae.culture"): castings * model.CASTINGS_TO_ALGAE,
        ("external.feedstock", "worms.breeder"): mean("feedstock_to_worms_kg"),
    }


def dependency_graph(practice: dict, path: Path | None = None) -> Path:
    """Stage graph. Line width follows the 1♂:3♀ median flow where a flow exists."""
    out = path or PLOTS / "cascade_dependency_graph.png"
    weights = _edge_weights(practice)
    positive = [v for v in weights.values() if v > 0]
    scale = max(positive) if positive else 1.0
    fig, ax = plt.subplots(figsize=(13.6, 7.4))
    ax.set_xlim(-0.35, 15.15)
    ax.set_ylim(0.35, 6.15)
    ax.axis("off")
    ax.set_title("Cascade dependency graph — life-cycle stages and nutrient links", color=INK, loc="left")

    for index, edge in enumerate(model.COUPLINGS):
        src = model.NODE_LAYOUT[edge["src"]]
        dst = model.NODE_LAYOUT[edge["dst"]]
        weight = weights.get((edge["src"], edge["dst"]), 0.0)
        width = 0.7 + (2.4 * weight / scale if weight > 0 else 0.0)
        color = KIND_COLOR.get(edge["kind"], MUTED)
        style = "--" if edge["kind"] == "competition" else "-"
        rad = 0.18 if index % 2 == 0 else -0.12
        if edge["kind"] == "maturation":
            rad = 0.0
        ax.annotate(
            "",
            xy=(dst[0], dst[1]),
            xytext=(src[0], src[1]),
            arrowprops={
                "arrowstyle": "-|>",
                "color": color,
                "lw": width,
                "ls": style,
                "connectionstyle": f"arc3,rad={rad}",
                "shrinkA": 16,
                "shrinkB": 16,
            },
            zorder=1,
        )

    for _node, (x, y, label, group) in model.NODE_LAYOUT.items():
        box = FancyBboxPatch(
            (x - 0.52, y - 0.34),
            1.04,
            0.68,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            facecolor=model.GROUP_COLOR[group],
            edgecolor=INK,
            linewidth=0.6,
            zorder=2,
        )
        ax.add_patch(box)
        ax.text(x, y, label, ha="center", va="center", fontsize=7.2, color=INK, zorder=3)

    handles = [
        plt.Line2D([0], [0], color=color, lw=2.0, label=kind)
        for kind, color in KIND_COLOR.items()
    ]
    ax.legend(handles=handles, frameon=False, loc="lower right", ncol=3, fontsize=8)
    _finish(
        fig,
        out,
        "Boxes are life-cycle stages. Arrows are fecundity, maturation, feed, manure, nutrients, or manure competition.\n"
        "Thicker arrows are the larger median weekly flows in the 1♂:3♀ run (weeks 20–40). Sex is drawn for quail and fish only.\n"
        "Worms are hermaphrodites. Stage 4 planning. Not a purchase. Stage 1 worms remain the only spend.",
    )
    return out


def _band(ax, weeks, series, color, label):
    ax.fill_between(weeks, series["p10"], series["p50"], color=color, alpha=0.18, linewidth=0)
    ax.plot(weeks, series["p50"], color=color, lw=2.0, label=label)
    ax.plot(weeks, series["p10"], color=color, lw=1.0, ls="--")


def trajectories(practice: dict, path: Path | None = None) -> Path:
    """Median and P10 for the 1♂:3♀ founders. P10 is the harsh path, not a sale."""
    out = path or PLOTS / "cascade_trajectories.png"
    weeks = practice["weeks"]
    series = practice["series"]
    fig, axes = plt.subplots(2, 3, figsize=(11.2, 7.2), sharex=True)
    panels = [
        (axes[0, 0], "worm_biomass_kg", "Worm biomass (kg)", PRACTICE),
        (axes[0, 1], "cricket_adults", "Cricket adults", "#c2410c"),
        (axes[0, 2], "greens_canopy_kg", "Greens canopy (kg)", "#3f6212"),
        (axes[1, 0], "fish_total", "Fish headcount", "#4338ca"),
        (axes[1, 1], "algae_kg", "Algae (kg)", "#0f766e"),
        (axes[1, 2], "quail_total", "Quail headcount", PRACTICE),
    ]
    for ax, key, title, color in panels:
        _band(ax, weeks, series[key], color, "Median")
        ax.set_title(title, fontsize=11, color=INK)
        ax.tick_params(labelsize=8)
    axes[1, 2].plot(weeks, series["quail_breeder_females"]["p50"], color="#0f766e", lw=1.6, label="Breeder hens, median")
    axes[1, 2].legend(frameon=False, fontsize=8)
    for ax in axes[1, :]:
        ax.set_xlabel("Week")
    fig.suptitle(
        f"Coupled paths, {int(practice['quail_males0'])}♂:{int(practice['quail_females0'])}♀ quail founders"
        f"  ·  seed {practice['seed']}  ·  {practice['paths']} paths",
        fontsize=12,
        color=INK,
    )
    _finish(
        fig,
        out,
        "Solid line is the median path. Dashed line is P10, the 10th percentile across paths. The shaded band is the harsh-to-median range.\n"
        "P10 is not a quantity to sell. Weekly offtake inside each path is alpha times surplus above the breed floor.\n"
        "Worm noise uses the ops-dashboard sigma of 0.015, so that band is narrow. Stage 4 planning. Not a purchase.",
    )
    return out


def sex_ratio_sensitivity(practice: dict, male_heavy: dict, path: Path | None = None) -> Path:
    """Same 16 founders. 1♂:3♀ against 3♂:1♀."""
    out = path or PLOTS / "cascade_sex_ratio_sensitivity.png"
    weeks = practice["weeks"]
    fig, axes = plt.subplots(2, 3, figsize=(11.2, 7.4))
    overlays = [
        (axes[0, 0], "quail_breeder_females", "Breeder hens"),
        (axes[0, 1], "greens_canopy_kg", "Greens canopy (kg)"),
        (axes[0, 2], "cricket_adults", "Cricket adults"),
        (axes[1, 0], "protein_to_fish_kg", "Protein to fish (kg/week)"),
        (axes[1, 1], "manure_to_worms_kg", "Quail manure into worms (kg/week)"),
    ]
    for ax, key, title in overlays:
        ax.plot(weeks, practice["series"][key]["p50"], color=PRACTICE, lw=2.0, label="1♂:3♀ median")
        ax.plot(weeks, male_heavy["series"][key]["p50"], color=MALE_HEAVY, lw=2.0, label="3♂:1♀ median")
        ax.set_title(title, fontsize=11, color=INK)
        ax.tick_params(labelsize=8)
        ax.set_xlabel("Week")
    axes[0, 0].legend(frameon=False, fontsize=8)

    phase = axes[1, 2]
    for ens, color, label in (
        (practice, PRACTICE, "1♂:3♀"),
        (male_heavy, MALE_HEAVY, "3♂:1♀"),
    ):
        x = ens["series"]["quail_breeder_females"]["p50"]
        y = ens["series"]["greens_canopy_kg"]["p50"]
        phase.plot(x, y, color=color, lw=2.0, label=label)
        phase.scatter([x[0], x[26], x[-1]], [y[0], y[26], y[-1]], color=color, s=18, zorder=3)
    phase.set_xlabel("Breeder hens (median)")
    phase.set_ylabel("Greens canopy kg")
    phase.set_title("Phase: hens against greens", fontsize=11, color=INK)
    phase.legend(frameon=False, fontsize=8)
    fig.suptitle("Same 16 quail founders. Sex ratio changes the flock and the species it feeds on.", fontsize=12, color=INK)
    _finish(
        fig,
        out,
        "Both runs start at 16 quail. 1♂:3♀ is the jumbo Coturnix practice. 3♂:1♀ keeps the same heads and swaps the sexes.\n"
        "Dots on the phase panel are weeks 0, 26, and 52. More hens lay more eggs, eat the greens down, leave fewer crickets, and take a larger share of the protein that would have gone to fish.\n"
        "Worm biomass barely moves between the two: either flock takes the firm juvenile surplus. Stage 4 planning. Not a purchase.",
    )
    return out


def write_all(practice: dict, male_heavy: dict, folder: Path | None = None) -> list[Path]:
    if folder is not None:
        global PLOTS
        PLOTS = folder
    PLOTS.mkdir(parents=True, exist_ok=True)
    return [
        dependency_graph(practice),
        trajectories(practice),
        sex_ratio_sensitivity(practice, male_heavy),
    ]
