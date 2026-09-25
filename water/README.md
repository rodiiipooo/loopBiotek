# Water

Potable / process water network modeling.

| Artifact | Notes |
|----------|-------|
| `stub.inp` | Minimal valid **EPANET** network (reservoir + 2 junctions + 2 pipes) |

## Tools

- **EPANET** (CLI / GUI) — hydraulic + water quality
- **QEPANET** / **QGISRed** — edit networks inside QGIS
- **WNTR** — installed in `/workspace/loopBiotek/.venv` for Python workflows

```bash
source /workspace/loopBiotek/.venv/bin/activate
python -c "import wntr; wn=wntr.network.WaterNetworkModel('water/stub.inp'); print(wn.junction_name_list)"
```
