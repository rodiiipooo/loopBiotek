#!/usr/bin/env python3
"""Create a minimal earth-sheltered Zone-1 cell IFC (IfcOpenShell).

Writes: buildings/models/zone1_cell_v1.ifc

Defaults (aligned with climate thermal-model cell):
  plan ~10 m × 10 m, storey height 3.0 m, earth-shelter annotation (sim baseline 70%).
"""
from __future__ import annotations

import sys
from pathlib import Path

import ifcopenshell
import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.project
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.unit

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "buildings" / "models" / "zone1_cell_v1.ifc"

LENGTH = 10.0
WIDTH = 10.0
STOREY_HEIGHT = 3.0
WALL_THICKNESS = 0.3
SUBMERSION_PCT = 70.0  # sim baseline; design min 50


def add_box(model, body, storey, product, name, dx, dy, dz, z0=0.0, x0=0.0, y0=0.0):
    """Attach an axis-aligned extruded box (meters) and contain in storey."""
    profile = model.create_entity(
        "IfcRectangleProfileDef",
        ProfileType="AREA",
        ProfileName=f"{name}_profile",
        XDim=float(dx),
        YDim=float(dy),
    )
    zdir = model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
    xdir = model.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0, 0.0))
    position = model.create_entity(
        "IfcAxis2Placement3D",
        Location=model.create_entity(
            "IfcCartesianPoint",
            Coordinates=(float(x0 + dx / 2), float(y0 + dy / 2), float(z0)),
        ),
        Axis=zdir,
        RefDirection=xdir,
    )
    solid = model.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profile,
        Position=position,
        ExtrudedDirection=zdir,
        Depth=float(dz),
    )
    shape_rep = model.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=body,
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=[solid],
    )
    product.Representation = model.create_entity(
        "IfcProductDefinitionShape", Representations=[shape_rep]
    )
    ifcopenshell.api.spatial.assign_container(
        model, relating_structure=storey, products=[product]
    )
    return product


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    model = ifcopenshell.api.project.create_file(version="IFC4")
    project = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcProject", name="LoopBiotek Zone1 Cell"
    )
    ifcopenshell.api.unit.assign_unit(model)

    model3d = ifcopenshell.api.context.add_context(model, context_type="Model")
    body = ifcopenshell.api.context.add_context(
        model,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=model3d,
    )

    site = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcSite", name="LoopBiotek 10-acre Ref"
    )
    building = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcBuilding", name="Zone1 Earth Habitat Cell"
    )
    storey = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcBuildingStorey", name="Level 1 (earth-sheltered)"
    )
    storey.Elevation = 0.0

    ifcopenshell.api.aggregate.assign_object(model, relating_object=project, products=[site])
    ifcopenshell.api.aggregate.assign_object(model, relating_object=site, products=[building])
    ifcopenshell.api.aggregate.assign_object(model, relating_object=building, products=[storey])

    slab = ifcopenshell.api.root.create_entity(model, ifc_class="IfcSlab", name="Cell Floor Slab")
    add_box(model, body, storey, slab, "slab", LENGTH, WIDTH, 0.2, z0=-0.2)

    # South / North / West / East walls
    specs = [
        ("Wall South", "ws", LENGTH, WALL_THICKNESS, 0.0, 0.0),
        ("Wall North", "wn", LENGTH, WALL_THICKNESS, 0.0, WIDTH - WALL_THICKNESS),
        ("Wall West", "ww", WALL_THICKNESS, WIDTH - 2 * WALL_THICKNESS, 0.0, WALL_THICKNESS),
        (
            "Wall East",
            "we",
            WALL_THICKNESS,
            WIDTH - 2 * WALL_THICKNESS,
            LENGTH - WALL_THICKNESS,
            WALL_THICKNESS,
        ),
    ]
    for wall_name, key, dx, dy, x0, y0 in specs:
        wall = ifcopenshell.api.root.create_entity(model, ifc_class="IfcWall", name=wall_name)
        add_box(model, body, storey, wall, key, dx, dy, STOREY_HEIGHT, z0=0.0, x0=x0, y0=y0)

    roof = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcRoof", name="Glazed Roof (water-loop plane)"
    )
    add_box(model, body, storey, roof, "roof", LENGTH, WIDTH, 0.15, z0=STOREY_HEIGHT)

    pset = ifcopenshell.api.pset.add_pset(
        model, product=building, name="Pset_LoopBiotek_EarthShelter"
    )
    ifcopenshell.api.pset.edit_pset(
        model,
        pset=pset,
        properties={
            "SubmersionPercent": SUBMERSION_PCT,
            "DesignMinSubmersionPercent": 50.0,
            "CellLength_m": LENGTH,
            "CellWidth_m": WIDTH,
            "StoreyHeight_m": STOREY_HEIGHT,
            "Zone": "zone1",
            "Version": "v1",
        },
    )

    pset_s = ifcopenshell.api.pset.add_pset(
        model, product=storey, name="Pset_LoopBiotek_Storey"
    )
    ifcopenshell.api.pset.edit_pset(
        model,
        pset=pset_s,
        properties={"StoreyHeight_m": STOREY_HEIGHT, "HasWindowOpening": False},
    )

    model.write(str(OUT))
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
    print(
        f"  plan={LENGTH}x{WIDTH} m, storey_height={STOREY_HEIGHT} m, "
        f"submersion={SUBMERSION_PCT:g}%"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
