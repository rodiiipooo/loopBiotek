# Building agents / MCP

Pointers for IFC-editing agent tooling (install separately as needed):

| Tool | Role |
|------|------|
| **MCP4IFC** | MCP server exposing IFC query/edit operations |
| **Bonsai_mcp** | Bridge agent actions into FreeCAD/Bonsai sessions |
| **ifcx-mcp** | Lightweight IFC / ifcx MCP surface for agents |

Local proof-of-edit without MCP: `../scripts/create_zone1_cell.py` and `edit_zone1_cell.py` using **IfcOpenShell** in the project venv.
