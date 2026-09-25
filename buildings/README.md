# Buildings

**IFC is the source of record (SoR)** for geometry and building semantics.

| Rule | Detail |
|------|--------|
| SoR | `.ifc` / IFC4 (or IFC2x3) under `models/` |
| Edit | FreeCAD + **Bonsai** (formerly BlenderBIM), or agent scripts via IfcOpenShell |
| AutoCAD | **DXF bridge only** — never treat DWG as SoR |
| Agents | See `agents/README.md` and root `AGENTS.md` |

## Scripts

```bash
cd /workspace/loopBiotek
.venv/bin/python buildings/scripts/create_zone1_cell.py   # → models/zone1_cell_v1.ifc
.venv/bin/python buildings/scripts/edit_zone1_cell.py     # → models/zone1_cell_v2.ifc
```

See `PROOF.md` for the proven create → edit chain.
