#!/usr/bin/env python3
"""Agent-style edit of Zone-1 cell IFC.

Reads:  buildings/models/zone1_cell_v1.ifc
Writes: buildings/models/zone1_cell_v2.ifc

Changes applied (documented in buildings/PROOF.md):
  1. Storey clear height 3.0 m → 3.5 m (extrude walls + raise roof solid).
  2. Add an IfcOpeningElement / window-style opening property on the South wall
     and set HasWindowOpening=True on the storey pset.
  3. Bump Version property to v2.
"""
from __future__ import annotations

import sys
from pathlib import Path

import ifcopenshell
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.util.element

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "buildings" / "models" / "zone1_cell_v1.ifc"
OUT = ROOT / "buildings" / "models" / "zone1_cell_v2.ifc"

OLD_H = 3.0
NEW_H = 3.5


def _wall_extrusions(model):
    """Yield (wall, extruded_area_solid) for IfcWall entities."""
    for wall in model.by_type("IfcWall"):
        if not wall.Representation:
            continue
        for rep in wall.Representation.Representations:
            for item in rep.Items:
                if item.is_a("IfcExtrudedAreaSolid"):
                    yield wall, item


def _roof_extrusions(model):
    for roof in model.by_type("IfcRoof"):
        if not roof.Representation:
            continue
        for rep in roof.Representation.Representations:
            for item in rep.Items:
                if item.is_a("IfcExtrudedAreaSolid"):
                    yield roof, item


def main() -> int:
    if not SRC.exists():
        print(f"Missing {SRC}; run create_zone1_cell.py first", file=sys.stderr)
        return 1

    model = ifcopenshell.open(str(SRC))

    # 1) Raise wall extrusions from 3.0 → 3.5 m
    for wall, solid in _wall_extrusions(model):
        if abs(float(solid.Depth) - OLD_H) < 1e-6:
            solid.Depth = NEW_H
            print(f"  wall '{wall.Name}': Depth {OLD_H} → {NEW_H} m")

    # 2) Raise roof base Z by +0.5 m (storey height delta)
    delta = NEW_H - OLD_H
    for roof, solid in _roof_extrusions(model):
        loc = solid.Position.Location
        x, y, z = [float(c) for c in loc.Coordinates]
        loc.Coordinates = (x, y, z + delta)
        print(f"  roof '{roof.Name}': z {z:.3f} → {z + delta:.3f} m")

    # 3) Add window opening on South wall + property flags
    south = next((w for w in model.by_type("IfcWall") if w.Name == "Wall South"), None)
    body = None
    for ctx in model.by_type("IfcGeometricRepresentationSubContext"):
        if ctx.ContextIdentifier == "Body":
            body = ctx
            break
    if body is None:
        for ctx in model.by_type("IfcGeometricRepresentationContext"):
            body = ctx
            break

    if south is not None and body is not None:
        opening = ifcopenshell.api.root.create_entity(
            model, ifc_class="IfcOpeningElement", name="South Window Opening"
        )
        # 1.2 m wide × 1.0 m high opening centered on south wall face
        profile = model.create_entity(
            "IfcRectangleProfileDef",
            ProfileType="AREA",
            ProfileName="south_window_profile",
            XDim=1.2,
            YDim=0.35,
        )
        zdir = model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
        xdir = model.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0, 0.0))
        position = model.create_entity(
            "IfcAxis2Placement3D",
            Location=model.create_entity(
                "IfcCartesianPoint", Coordinates=(5.0, 0.15, 1.0)
            ),
            Axis=zdir,
            RefDirection=xdir,
        )
        solid = model.create_entity(
            "IfcExtrudedAreaSolid",
            SweptArea=profile,
            Position=position,
            ExtrudedDirection=zdir,
            Depth=1.0,
        )
        shape_rep = model.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=body,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid",
            Items=[solid],
        )
        opening.Representation = model.create_entity(
            "IfcProductDefinitionShape", Representations=[shape_rep]
        )
        # Relate opening to wall
        model.create_entity(
            "IfcRelVoidsElement",
            GlobalId=ifcopenshell.guid.new(),
            RelatingBuildingElement=south,
            RelatedOpeningElement=opening,
        )
        print(f"  added IfcOpeningElement '{opening.Name}' voiding '{south.Name}'")

        # Optional window element filling the opening
        window = ifcopenshell.api.root.create_entity(
            model, ifc_class="IfcWindow", name="South Window"
        )
        window.OverallHeight = 1.0
        window.OverallWidth = 1.2
        model.create_entity(
            "IfcRelFillsElement",
            GlobalId=ifcopenshell.guid.new(),
            RelatingOpeningElement=opening,
            RelatedBuildingElement=window,
        )
        storey = model.by_type("IfcBuildingStorey")[0]
        ifcopenshell.api.spatial.assign_container(
            model, relating_structure=storey, products=[window]
        )
        print(f"  added IfcWindow '{window.Name}' 1.2×1.0 m")

    # 4) Update property sets
    building = model.by_type("IfcBuilding")[0]
    storey = model.by_type("IfcBuildingStorey")[0]

    psets_b = ifcopenshell.util.element.get_psets(building)
    if "Pset_LoopBiotek_EarthShelter" in psets_b:
        pset = next(
            d
            for d in model.by_type("IfcPropertySet")
            if d.Name == "Pset_LoopBiotek_EarthShelter"
        )
        ifcopenshell.api.pset.edit_pset(
            model,
            pset=pset,
            properties={"StoreyHeight_m": NEW_H, "Version": "v2"},
        )

    psets_s = ifcopenshell.util.element.get_psets(storey)
    if "Pset_LoopBiotek_Storey" in psets_s:
        pset = next(
            d
            for d in model.by_type("IfcPropertySet")
            if d.Name == "Pset_LoopBiotek_Storey"
        )
        ifcopenshell.api.pset.edit_pset(
            model,
            pset=pset,
            properties={"StoreyHeight_m": NEW_H, "HasWindowOpening": True},
        )
    else:
        pset = ifcopenshell.api.pset.add_pset(
            model, product=storey, name="Pset_LoopBiotek_Storey"
        )
        ifcopenshell.api.pset.edit_pset(
            model,
            pset=pset,
            properties={"StoreyHeight_m": NEW_H, "HasWindowOpening": True},
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    model.write(str(OUT))
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
    print(f"  CHANGE: storey height {OLD_H} → {NEW_H} m; added south window opening")
    return 0


if __name__ == "__main__":
    sys.exit(main())
