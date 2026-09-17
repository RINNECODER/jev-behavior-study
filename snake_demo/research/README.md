# Classic Snake research

[Read the findings](REPORT.md) · [Interactive replay](https://rinnecoder.github.io/jev-behavior-study/snake_demo/web/classic.html) · [Frozen protocol](PROTOCOL.md) · [Adaptive amendments](AMENDMENTS.md)

This study distinguishes model decision quality from algorithmic assistance.
A perfect observed eight-food benchmark is not a universal Snake guarantee.

## Live improved controller

From the repository root, set `TYPESAFE_API_KEY` in your environment or ignored
root `.env`, then run:

```bash
python -m snake_demo.research.server
```

Open http://127.0.0.1:8766/, choose **Live**, then **Jev + exact route facts** or
**Jev + route facts + verifier** and press **Start live**. Each move makes one
paid model request. The board waits for the response. Pause stops further calls.
The code-only profile uses no model. Fresh live logs are ignored and excluded
from study counts. The public GitHub Pages site provides recorded replays only.

## Verify offline (no model calls)

```bash
python -m unittest snake_demo.test_snake snake_demo.research.test_oracle
python -m snake_demo.research.analyze snake_demo/research/records/diagnosis-v1
python -m snake_demo.research.verify_games snake_demo/research/records/gameplay-v1
python -m snake_demo.research.verify_games snake_demo/research/records/stress-v1
python -m snake_demo.research.verify_games snake_demo/research/records/long-planner-v1
python -m snake_demo.research.verify_long_v2 snake_demo/research/records/long-v2-development
python -m snake_demo.research.verify_long_v2 snake_demo/research/records/long-v2-holdout
python -m snake_demo.research.build_report
```

The old Classic audit can be regenerated with `python -m snake_demo.research.analyze`
(no argument). Full verification of longer-body searches can take minutes.

Rebuild the viewer dataset after verifying gameplay:

```python
import json
from pathlib import Path
p = Path('snake_demo/research/records/gameplay-v1')
data = {'metrics': json.loads((p/'analysis.json').read_text()),
        'runs': json.loads((p/'verified_replays.json').read_text())}
Path('snake_demo/web/research-data.js').write_text(
    'window.CLASSIC_DATA = ' + json.dumps(data, separators=(',', ':')) + ';\n')
```

## Run a new paid fixed-state study

Use a new output directory. The corpus generator uses the published original
records and deterministic seed rules. The 924-call plan is written before calls:

```bash
python -m snake_demo.research.experiment prepare /tmp/new-classic-study
python -m snake_demo.research.experiment run /tmp/new-classic-study
python -m snake_demo.research.analyze /tmp/new-classic-study
```

`run` loads the repository's ignored `.env` or uses the environment. Existing
job records are preserved on resume, including failures; nothing is retried.
To run new held-out gameplay after that analysis, import `prepare` and `run`
from `snake_demo.research.gameplay`, pass a new output directory to `prepare`
alongside the diagnosis directory, then pass the output directory to `run`.
It uses 64 games and at most 9,600 model calls. See the frozen protocol before
changing seeds, rules or selection. Never overwrite or merge a new run into the
published counts.

## Files and roles

- `oracle.py`: full per-action dynamic-body A*, independent BFS reference.
- `efficient.py`: adaptive bounded-certificate search repair.
- `experiment.py`: fixed-state variants, option permutations and atomic checks.
- `gameplay.py`: held-out full games and original code-only stress tests.
- `long_v2.py`: separately amended longer-game code tests and conditional gate.
- `analyze.py`, `verify_games.py`, `verify_long_v2.py`: evidence verification.
- `server.py`: live eight-food research controller, local credentials only.
- `records/`: complete evidence, manifests, summaries and per-question CSVs.

V2 unknown search outcomes remain unknown. It is not permissible to count them
as either optimal moves or unavoidable collisions.
