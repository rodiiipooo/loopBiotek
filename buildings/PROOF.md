# Buildings proof — agent-editable IFC chain

Proven on the project box using `/workspace/loopBiotek/.venv` (IfcOpenShell 0.8.5).

## Commands

```bash
cd /workspace/loopBiotek
.venv/bin/python buildings/scripts/create_zone1_cell.py
.venv/bin/python buildings/scripts/edit_zone1_cell.py
```

## Outputs

| File | Absolute path | Size |
|------|---------------|------|
| v1 (create) | `/workspace/loopBiotek/buildings/models/zone1_cell_v1.ifc` | 4943 bytes |
| v2 (edit) | `/workspace/loopBiotek/buildings/models/zone1_cell_v2.ifc` | 5629 bytes |

## What changed (v1 → v2)

1. **Storey height** raised **3.0 m → 3.5 m**
   - All four `IfcWall` extrusions (`Wall South/North/West/East`): `Depth` 3.0 → 3.5
   - `IfcRoof` ("Glazed Roof") placement Z raised 3.0 → 3.5 so the roof stays on top of the taller walls
2. **South window opening added**
   - New `IfcOpeningElement` named `South Window Opening` voiding `Wall South` via `IfcRelVoidsElement`
   - New `IfcWindow` named `South Window` (OverallWidth=1.2 m, OverallHeight=1.0 m) filling the opening via `IfcRelFillsElement`
3. **Property sets updated**
   - `Pset_LoopBiotek_EarthShelter.StoreyHeight_m`: 3.0 → 3.5; `Version`: v1 → v2
   - `Pset_LoopBiotek_Storey.StoreyHeight_m`: 3.0 → 3.5; `HasWindowOpening`: False → True

Unchanged: plan 10×10 m, submersion annotation 70% (design min 50%), Zone=`zone1`.

## Why this matters

Agents (or MCP tools such as MCP4IFC / Bonsai_mcp / ifcx-mcp) can treat **IFC as SoR**, bump a versioned file, and leave a clear semantic diff — without ever making DWG the source of record.
