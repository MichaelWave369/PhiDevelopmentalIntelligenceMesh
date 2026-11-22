# Φ Developmental Intelligence Mesh

**More crayons. Better books. Constructive feedback. Room to grow.**

A small, offline, open-source experimental framework that brings together ideas
from four existing projects without fusing or overwriting their code:

- **PhiGrowthLab:** investigate structural growth, pruning, replay, forgetting.
- **Sovereign Intelligence Mesh:** local AI workspace; read-only status bridge.
- **PhiBuddy Rust:** council review; manual evidence packet + read-only counts.
- **PhiEmergence / Phi Coherence Lab:** independent mathematical worlds and
  physical-model controls; read-only source-data validation.

**Current capability is an associative learner, not a developing human brain.**
It does not claim consciousness, autonomy, biological neurons, or LLM weight updates.

## Quick start (Python 3.10+; no dependencies)

```bash
python -m unittest discover -s tests -v
python -m devmesh benchmark --seed 369 --output outputs/seed-369
```

Open `outputs/seed-369/report.html` in a browser (works offline), inspect
`results.json`, and hand `review_packet.md` to a human or PhiBuddy for review.

### Teach one example (explicit, approved, local)

```bash
python -m devmesh teach --db data/learner.sqlite --world shapes --source triangle --dest 3-sides
python -m devmesh inspect --db data/learner.sqlite
```

### Optional bridges (never run without you invoking them)

```bash
# Sovereign Mesh must already be running on this machine
python -m devmesh mesh-status --url http://127.0.0.1:4765

# Original PhiEmergence v1.0 export folder (unaltered)
python -m devmesh validate-emergence --folder ../PhiEmergence_v1.0

# Original Coherence Lab CSV (unaltered)
python -m devmesh inspect-coherence --csv ../phi_coherence_lab/transport_results.csv

# Your own PhiBuddy Rust database, counts only (no message text)
python -m devmesh inspect-buddy --db /path/to/buddy.sqlite3
```

No model runtime is required for the benchmark. No upstream projects or user
chat histories are automatically imported. Original projects remain separately
licensed; this repository contains only newly-authored integration code.

See [architecture](docs/ARCHITECTURE.md) and [research protocol](docs/RESEARCH_PROTOCOL.md).

## Ethics and limits

Developmental stages are a **software metaphor**: an artificial learner does
not grow up like a child. Results are reproducible programming experiments,
not evidence of artificial sentience or new physics. Human feedback is
recorded explicitly; independent held-out validation prevents grading on
lessons the system has memorized.

Open-source MIT license. Built for local-first, auditable experiments.
