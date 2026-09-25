# Power

Electrical distribution + PV stubs for the Loop farm.

| Artifact | Notes |
|----------|-------|
| `stub.dss` | Minimal **OpenDSS** circuit (source + line + load + optional PV) |

## Tools

- **OpenDSS** / **OpenDSSDirect.py** (in `.venv`) — distribution power flow
- **GridLAB-D** — multi-timescale / co-sim (install separately)
- **pvlib** — irradiance → PV yield (install when sizing canopy PV)

Energy grounding from Loop report: ~**41 kWh/day** for a 2-cell farm; ~**12%** save from earth-sheltering.

```bash
source /workspace/loopBiotek/.venv/bin/activate
python -c "import opendssdirect as dss; dss.Text.Command('Redirect power/stub.dss'); print(dss.Circuit.TotalPower())"
```
