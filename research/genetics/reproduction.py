#!/usr/bin/env python3
"""Pedigree and inbreeding haircuts for quail and aquaponics fish. Planning only.

Stage 1 worms remain the spend source of record. Quail is Stage 4 planning.
Fish is Stage 5 (aquaponics) planning. Nothing here authorizes a purchase.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

_SYNERGY = Path(__file__).resolve().parents[1] / "synergy"
if str(_SYNERGY) not in sys.path:
    sys.path.insert(0, str(_SYNERGY))

try:
    from circular_buffers import breed_floor  # noqa: E402
except ImportError as err:
    raise ImportError(
        "This folder expects research/synergy next to it. Clone the whole repository, "
        "then run from research/genetics."
    ) from err

# FAO short-term rule: keep the inbreeding rate at or under 1% per generation,
# which needs Ne >= 50. Long-term Ne of about 500 is documented and not the default.
DELTA_F_MAX = 0.01
F_MAX = 0.0
FULL_SIB_F = 0.25

# Quail hatch baseline matches research/quail (ASSUMPTION midpoint used there).
QUAIL_HATCH0 = 0.75

# Percentage-point drop per 0.10 of F. Sato and colleagues, full-sib vs random
# mating in Japanese quail (Jpn. J. Zootech. Sci. 55:315). Egg rate is a
# different study (incross lines) and is tagged separately in SPECIES.
QUAIL_POINTS_PER_10 = {
    "fertility": 0.0216,
    "hatch": 0.0598,
    "viability": 0.0550,
    "egg_rate": 0.0338,
}
# No carcass-grade regression in those papers.
QUAIL_REJECT_POINTS_PER_10 = 0.02

# Fish coefficients are planning placeholders, not a measured aquaponics stock.
# They are relative losses of the baseline trait per 0.10 of F.
FISH_RELATIVE_PER_10 = {
    "hatch": 0.05,
    "growth": 0.03,
    "fecundity": 0.05,
    "viability": 0.05,
}
FISH_REJECT_POINTS_PER_10 = 0.03
FISH_HATCH0 = 0.80  # ASSUMPTION baseline so the haircut has a number


def wright_ne(n_males: float, n_females: float) -> float:
    """Wright's sex-ratio effective size: Ne = 4 Nm Nf / (Nm + Nf).

    Idealized: random mating, no selection, Poisson family size.
    """
    nm = float(n_males)
    nf = float(n_females)
    if nm < 0 or nf < 0:
        raise ValueError("breeder counts must be >= 0")
    if nm + nf == 0:
        return 0.0
    return 4.0 * nm * nf / (nm + nf)


def delta_f(ne: float) -> float:
    """Inbreeding added in one generation: ΔF = 1 / (2 Ne)."""
    if ne < 0:
        raise ValueError("Ne must be >= 0")
    if ne == 0:
        return 1.0
    return 1.0 / (2.0 * ne)


def ne_min_for(delta_f_max: float = DELTA_F_MAX) -> float:
    """Smallest Ne whose ΔF is at or under the cap. Ne = 1 / (2 ΔF)."""
    if not 0 < delta_f_max < 1:
        raise ValueError("delta_f_max must be in (0, 1)")
    return 1.0 / (2.0 * delta_f_max)


def minimum_breeders(ne_min: float, females_per_male: float) -> tuple[int, int]:
    """Smallest whole-animal male and female counts that reach ne_min at this ratio."""
    if ne_min <= 0:
        raise ValueError("ne_min must be > 0")
    if females_per_male <= 0:
        raise ValueError("females_per_male must be > 0")
    rho = float(females_per_male)
    nm = max(1, math.ceil(ne_min * (1.0 + rho) / (4.0 * rho) - 1e-12))
    nf = max(1, math.ceil(nm * rho - 1e-12))
    while wright_ne(nm, nf) + 1e-9 < ne_min:
        if nm / max(nf, 1) < 1.0 / rho:
            nm += 1
        else:
            nf += 1
    return nm, nf


class Animal:
    def __init__(self, id: str, sex: str, sire: str | None = None, dam: str | None = None) -> None:
        if sex not in ("M", "F"):
            raise ValueError("sex must be M or F")
        self.id = id
        self.sex = sex
        self.sire = sire
        self.dam = dam


def _order_animals(animals: list[Animal]) -> list[Animal]:
    by_id = {a.id: a for a in animals}
    if len(by_id) != len(animals):
        raise ValueError("animal ids must be unique")
    pending = {a.id for a in animals}
    ordered: list[Animal] = []
    while pending:
        ready = [
            i
            for i in pending
            if (by_id[i].sire is None or by_id[i].sire not in pending)
            and (by_id[i].dam is None or by_id[i].dam not in pending)
        ]
        if not ready:
            raise ValueError("pedigree has a cycle")
        ready.sort()
        for i in ready:
            ordered.append(by_id[i])
            pending.remove(i)
    return ordered


def numerator_relationship(animals: list[Animal]) -> dict[tuple[str, str], float]:
    """Tabular numerator relationship. Parents before offspring.

    Offspring inbreeding for a mating is half the relationship of the two parents.
    An id named as a parent but missing from `animals` is treated as an outside
    founder, relationship 0 to everyone listed. That can hide kinship.
    """
    ordered = _order_animals(animals)
    ids = {a.id for a in ordered}
    rel: dict[tuple[str, str], float] = {}

    def a_of(i: str, j: str) -> float:
        if i == j:
            return rel.get((i, i), 0.0)
        return rel.get((i, j), rel.get((j, i), 0.0))

    for animal in ordered:
        sire = animal.sire if animal.sire in ids else None
        dam = animal.dam if animal.dam in ids else None
        f_self = 0.0 if sire is None or dam is None else 0.5 * a_of(sire, dam)
        rel[(animal.id, animal.id)] = 1.0 + f_self
        for earlier in ordered:
            if earlier.id == animal.id:
                break
            left = 0.0 if sire is None else a_of(sire, earlier.id)
            right = 0.0 if dam is None else a_of(dam, earlier.id)
            value = 0.5 * (left + right)
            rel[(animal.id, earlier.id)] = value
            rel[(earlier.id, animal.id)] = value
    return rel


def offspring_f(rel: dict[tuple[str, str], float], sire: str, dam: str) -> float:
    """Inbreeding coefficient of an offspring of this pair. F = a_sd / 2."""
    return 0.5 * rel.get((sire, dam), rel.get((dam, sire), 0.0))


def pedigree_gaps(animals: list[Animal]) -> list[str]:
    """Parent ids that are named but not present in the book."""
    ids = {a.id for a in animals}
    gaps = []
    for animal in animals:
        for parent in (animal.sire, animal.dam):
            if parent is not None and parent not in ids:
                gaps.append(parent)
    return sorted(set(gaps))


def mating_allowed(f_offspring: float, f_max: float = F_MAX) -> bool:
    """Strict rule. Default f_max = 0 refuses every pair with kinship above unrelated."""
    if f_max < 0 or f_max > 1:
        raise ValueError("f_max must be in [0, 1]")
    return f_offspring <= f_max + 1e-12


def _clip01(value: float) -> float:
    return min(1.0, max(0.0, value))


def trait_after_f(baseline: float, f_bar: float, per_10: float, how: str) -> float:
    """Apply one haircut.

    how='points': baseline and per_10 are on the same 0–1 scale. per_10 is the
    drop for each 0.10 of F (Sato-style percentage points).
    how='relative': per_10 is the fraction of baseline lost for each 0.10 of F.
    """
    if f_bar < 0:
        raise ValueError("F must be >= 0")
    if how == "points":
        return _clip01(baseline - per_10 * (f_bar / 0.10))
    if how == "relative":
        return _clip01(baseline * (1.0 - per_10 * (f_bar / 0.10)))
    raise ValueError("how must be points or relative")


def mean_f(x_inbred: float | None, f_bar: float | None, f_of_inbred_class: float = FULL_SIB_F) -> float:
    """Mean offspring F. Pass F_bar directly, or the fraction x that are inbred at f_of_inbred_class."""
    if f_bar is not None and x_inbred is not None:
        raise ValueError("pass F_bar or x_inbred, not both")
    if f_bar is None and x_inbred is None:
        raise ValueError("pass F_bar or x_inbred")
    if f_bar is not None:
        if not 0 <= f_bar <= 1:
            raise ValueError("F_bar must be in [0, 1]")
        return float(f_bar)
    if not 0 <= x_inbred <= 1:
        raise ValueError("x_inbred must be in [0, 1]")
    if not 0 <= f_of_inbred_class <= 1:
        raise ValueError("f_of_inbred_class must be in [0, 1]")
    return float(x_inbred) * float(f_of_inbred_class)


def leakage(
    species: str,
    f_bar: float | None = None,
    x_inbred: float | None = None,
    f_of_inbred_class: float = FULL_SIB_F,
    hatch0: float | None = None,
    reject0: float = 0.0,
) -> dict:
    """Haircut hatch, growth or viability, fecundity, and the reject rate.

    Linear in F. Quail uses measured percentage-point slopes. Fish uses
    ASSUMPTION relative slopes. The outbred part of a mix is F = 0, so
    F_bar = x * F_of_the_inbred_class.
    """
    if species not in ("quail", "fish"):
        raise ValueError("species must be quail or fish")
    if not 0 <= reject0 <= 1:
        raise ValueError("reject0 must be in [0, 1]")
    f = mean_f(x_inbred, f_bar, f_of_inbred_class)
    if species == "quail":
        h0 = QUAIL_HATCH0 if hatch0 is None else hatch0
        how = "points"
        slopes = QUAIL_POINTS_PER_10
        reject_per_10 = QUAIL_REJECT_POINTS_PER_10
        tag = {
            "hatch": "SOURCED",
            "fertility": "SOURCED",
            "viability": "SOURCED",
            "egg_rate": "SOURCED_OTHER_STUDY",
            "reject": "ASSUMPTION",
        }
        stage = "Stage 4 quail planning. Not spend."
    else:
        h0 = FISH_HATCH0 if hatch0 is None else hatch0
        how = "relative"
        slopes = FISH_RELATIVE_PER_10
        reject_per_10 = FISH_REJECT_POINTS_PER_10
        tag = {name: "ASSUMPTION" for name in ("hatch", "growth", "fecundity", "viability", "reject")}
        stage = "Stage 5 aquaponics fish planning. Not spend."
    fecundity_key = "fertility" if species == "quail" else "fecundity"
    growth_key = "viability" if species == "quail" else "growth"
    hatch = trait_after_f(h0, f, slopes["hatch"], how)
    fecundity = trait_after_f(1.0, f, slopes[fecundity_key], how)
    growth = trait_after_f(1.0, f, slopes[growth_key], how)
    egg = None
    if species == "quail":
        egg = trait_after_f(1.0, f, slopes["egg_rate"], how)
    reject = _clip01(reject0 + reject_per_10 * (f / 0.10))
    return {
        "species": species,
        "stage": stage,
        "F_bar": f,
        "x_inbred": x_inbred,
        "f_of_inbred_class": None if x_inbred is None else f_of_inbred_class,
        "how": how,
        "hatch": hatch,
        "hatch_baseline": h0,
        "fecundity_index": fecundity,
        "growth_index": growth,
        "egg_rate_index": egg,
        "reject_rate": reject,
        "saleable_fraction": _clip01(1.0 - reject),
        "tags": tag,
        "formula": (
            "F_bar = x * F_class when a fraction x is inbred; "
            "y = max(0, y0 - beta_10 * F/0.10) for quail points; "
            "y = y0 * max(0, 1 - b_10 * F/0.10) for fish relative haircuts"
        ),
    }


def keep_floor(
    n0: float,
    n_start: float | None,
    n_safety: float | None,
    females_per_male: float,
    delta_f_max: float = DELTA_F_MAX,
) -> dict:
    """Headcount that must stay: synergy breed floor, and the Ne floor, whichever is larger."""
    synergy = breed_floor(n0, n0 if n_start is None else n_start, n0 if n_safety is None else n_safety)
    need = ne_min_for(delta_f_max)
    nm, nf = minimum_breeders(need, females_per_male)
    genetics = nm + nf
    return {
        "synergy_floor": synergy,
        "ne_min": need,
        "males_min": nm,
        "females_min": nf,
        "genetics_floor": genetics,
        "keep": max(synergy, genetics),
        "delta_f_max": delta_f_max,
    }


def cull_plan(
    n_males: float,
    n_females: float,
    sell_males: float,
    sell_females: float,
    n0: float,
    females_per_male: float,
    n_start: float | None = None,
    n_safety: float | None = None,
    delta_f_max: float = DELTA_F_MAX,
    animals: list[Animal] | None = None,
    proposed_matings: list[tuple[str, str]] | None = None,
    f_max: float = F_MAX,
) -> dict:
    """Refuse a sale that breaks the synergy floor, the Ne floor, or the mating cap.

    Surplus is whatever remains after both floors. A pedigree, when given, must
    still contain at least one allowed pair, and every proposed pair must pass.
    """
    if sell_males < 0 or sell_females < 0:
        raise ValueError("sales must be >= 0")
    if sell_males > n_males + 1e-9 or sell_females > n_females + 1e-9:
        raise ValueError("cannot sell more animals than are on hand")
    floor = keep_floor(n0, n_start, n_safety, females_per_male, delta_f_max)
    nm = n_males - sell_males
    nf = n_females - sell_females
    ne = wright_ne(nm, nf)
    reasons: list[str] = []
    if nm + 1e-9 < floor["males_min"] or nf + 1e-9 < floor["females_min"]:
        reasons.append("sale would drop males or females under the Ne floor")
    if nm + nf + 1e-9 < floor["keep"]:
        reasons.append("sale would drop the herd under the breed floor")
    if ne + 1e-9 < floor["ne_min"]:
        reasons.append("sale would push ΔF above the cap")
    mating_notes: list[dict] = []
    if animals:
        gaps = pedigree_gaps(animals)
        if gaps:
            reasons.append("pedigree names parents that are not in the book")
        rel = numerator_relationship(animals)
        pairs = proposed_matings or []
        if not pairs:
            # One allowed pair is enough to show the remaining book can still mate.
            males = [a.id for a in animals if a.sex == "M"]
            females = [a.id for a in animals if a.sex == "F"]
            pairs = [(m, f) for m in males for f in females]
            legal = []
            for sire, dam in pairs:
                f_off = offspring_f(rel, sire, dam)
                if mating_allowed(f_off, f_max):
                    legal.append((sire, dam, f_off))
            if not legal:
                reasons.append("no remaining pair stays at or under the inbreeding cap")
            mating_notes.append({"legal_pairs": len(legal), "pairs_checked": len(pairs)})
        else:
            for sire, dam in pairs:
                f_off = offspring_f(rel, sire, dam)
                allowed = mating_allowed(f_off, f_max)
                mating_notes.append({"sire": sire, "dam": dam, "F": f_off, "allowed": allowed})
                if not allowed:
                    reasons.append(f"mating {sire} x {dam} has F={f_off:.4f} above the cap")
    allowed_sale = not reasons
    return {
        "allowed": allowed_sale,
        "reasons": reasons,
        "males_after": nm,
        "females_after": nf,
        "Ne_after": ne,
        "delta_F_after": delta_f(ne),
        "floor": floor,
        "matings": mating_notes,
        "f_max": f_max,
        "stage_gate": "Planning only. Stage 1 worms remain the only active spend.",
    }


def smoke(path: Path | None = None) -> dict:
    """Write results/reproduction_smoke.json. Raises if a check fails."""
    ne_equal = wright_ne(10, 10)
    ne_quail_ratio = wright_ne(10, 30)
    assert abs(ne_equal - 20) < 1e-9
    assert abs(ne_quail_ratio - 30) < 1e-9
    assert abs(delta_f(50) - 0.01) < 1e-12
    assert abs(ne_min_for(0.01) - 50) < 1e-9

    founders = [
        Animal("S", "M"),
        Animal("D", "F"),
        Animal("A", "M", "S", "D"),
        Animal("B", "F", "S", "D"),
        Animal("H", "F", "S", None),
    ]
    rel = numerator_relationship(founders)
    assert abs(offspring_f(rel, "S", "D")) < 1e-12
    assert mating_allowed(offspring_f(rel, "S", "D"), F_MAX)
    f_full = offspring_f(rel, "A", "B")
    assert abs(f_full - 0.25) < 1e-12
    assert not mating_allowed(f_full, F_MAX)
    f_half = offspring_f(rel, "A", "H")
    assert abs(f_half - 0.125) < 1e-12
    f_parent = offspring_f(rel, "A", "D")
    assert abs(f_parent - 0.25) < 1e-12

    quail_hatch = leakage("quail", f_bar=0.10)
    assert abs(quail_hatch["hatch"] - (QUAIL_HATCH0 - 0.0598)) < 1e-12
    mixed = leakage("quail", x_inbred=0.20, f_of_inbred_class=FULL_SIB_F)
    assert abs(mixed["F_bar"] - 0.05) < 1e-12
    assert mixed["hatch"] < QUAIL_HATCH0
    fish = leakage("fish", f_bar=0.10)
    assert abs(fish["growth_index"] - (1.0 - 0.03)) < 1e-12
    assert fish["tags"]["growth"] == "ASSUMPTION"
    assert quail_hatch["tags"]["hatch"] == "SOURCED"

    # 40 males and 120 females, synergy floor 20, Ne floor 50 at 1:3.
    # Selling down to Ne=30 is refused. Selling surplus that leaves Ne=90 is allowed.
    blocked = cull_plan(40, 120, 30, 90, n0=20, females_per_male=3)
    assert blocked["allowed"] is False
    assert blocked["Ne_after"] < 50
    spared = cull_plan(40, 120, 10, 30, n0=20, females_per_male=3)
    assert spared["allowed"] is True
    assert spared["floor"]["keep"] >= spared["floor"]["genetics_floor"]
    assert spared["floor"]["genetics_floor"] > spared["floor"]["synergy_floor"]

    sib_block = cull_plan(
        2,
        2,
        0,
        0,
        n0=1,
        females_per_male=1,
        delta_f_max=0.5,
        animals=[Animal("S", "M"), Animal("D", "F"), Animal("A", "M", "S", "D"), Animal("B", "F", "S", "D")],
        proposed_matings=[("A", "B")],
    )
    assert sib_block["allowed"] is False

    payload = {
        "ok": True,
        "stage_gate": "Stage 1 worms only. Quail is Stage 4 planning. Fish is Stage 5 planning. No Stage 2-5 spend.",
        "defaults": {
            "F_max": F_MAX,
            "delta_F_max": DELTA_F_MAX,
            "Ne_min": 50,
            "full_sib_F": FULL_SIB_F,
            "quail_points_per_0.10_F": QUAIL_POINTS_PER_10,
            "quail_reject_points_per_0.10_F": QUAIL_REJECT_POINTS_PER_10,
            "fish_relative_loss_per_0.10_F": FISH_RELATIVE_PER_10,
            "formulas": {
                "Ne": "4*Nm*Nf/(Nm+Nf)",
                "delta_F": "1/(2*Ne)",
                "offspring_F": "a_sire_dam/2",
                "F_bar": "x * F_class",
            },
        },
        "checks": {
            "Ne_10_10": ne_equal,
            "Ne_10_30": ne_quail_ratio,
            "delta_F_at_50": delta_f(50),
            "full_sib_F": f_full,
            "half_sib_F": f_half,
            "quail_hatch_at_F_0.10": quail_hatch["hatch"],
            "quail_F_bar_when_20pct_full_sib": mixed["F_bar"],
            "fish_growth_index_at_F_0.10": fish["growth_index"],
            "cull_to_Ne_30_allowed": blocked["allowed"],
            "cull_leaving_Ne_90_allowed": spared["allowed"],
            "genetics_floor_above_synergy_floor": spared["floor"]["genetics_floor"] > 20,
        },
    }
    out = path or Path(__file__).resolve().parent / "results" / "reproduction_smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = smoke()
    if not result["ok"]:
        raise SystemExit("reproduction smoke failed")
    checks = result["checks"]
    print(
        f"Ne(10,30)={checks['Ne_10_30']}  full_sib_F={checks['full_sib_F']}  "
        f"quail_hatch(F=0.10)={checks['quail_hatch_at_F_0.10']:.4f}  "
        f"cull_Ne30={checks['cull_to_Ne_30_allowed']}  cull_Ne90={checks['cull_leaving_Ne_90_allowed']}"
    )
