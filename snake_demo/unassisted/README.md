# Unassisted Jev Snake experiments

[Findings](REPORT.md) · [Protocol](PROTOCOL.md) · [Replay viewer](https://rinnecoder.github.io/jev-behavior-study/snake_demo/web/unassisted.html)

No route costs, safety flags, option filtering, fallback or corrections are
supplied. Each final model action executes unchanged. Offline labels never enter
a model request. The earlier assisted study remains separate evidence.

## Play live

From the repository root, set `TYPESAFE_API_KEY` in your environment or ignored
root `.env` and run:

```bash
python -m snake_demo.unassisted.server
```

Open http://127.0.0.1:8767/, select **Live**, choose the controller and press
**Start live**. These are fresh paid calls, one decision at a time. Pause stops
requesting further moves. The key stays server-side. Live logs are ignored and
excluded from study totals. The public viewer uses recorded games and no key.

## Verify and rebuild without paid calls

```bash
python -m unittest snake_demo.test_snake snake_demo.research.test_oracle snake_demo.unassisted.test_policy
python -m snake_demo.unassisted.analyze snake_demo/unassisted/records/screen-v1
python -m snake_demo.unassisted.analyze snake_demo/unassisted/records/development-v1
python -m snake_demo.unassisted.analyze snake_demo/unassisted/records/holdout-v1
python -m snake_demo.unassisted.build_report
```

Analysis recomputes labels and verifies the model's actual choices against the
engine. It makes no API requests. Model requests are single-question calls;
`per_question.csv` preserves input/output tokens for each proposal or review call.

## Repeat the study with new paid calls

Use new output directories. This Python example runs screening, selection,
development games and final games; set the API key first. It reproduces the
published seed design, so it is a replication rather than a new unseen-seed test.
Inspect [PROTOCOL.md](PROTOCOL.md) before execution; the conservative bound is
26,320 requests. No request retries or replacements are performed.

```python
from pathlib import Path
from snake_demo.unassisted.run import prepare_screen, run_screen, prepare_games, run_games
from snake_demo.unassisted.analyze import screen, games

base = Path('/tmp/jev-unassisted-replication')
screen_dir, dev_dir, test_dir = (base/x for x in ['screen', 'development', 'holdout'])
prepare_screen(screen_dir)
run_screen(screen_dir)
s = screen(screen_dir)
prepare_games(dev_dir, ['original'] + s['selected'], range(8101,8105),
              'development_games', {'selected': s['selected']})
run_games(dev_dir)
d = games(dev_dir)
prepare_games(test_dir, ['original'] + d['selected'], range(9101,9117),
              'heldout_games', {'selected': d['selected']})
run_games(test_dir)
games(test_dir)
```

Existing output directories/call files are refused to avoid replacing evidence.
Each stage's manifest is written before that stage's calls. The published report
builder intentionally points at the frozen study directories; do not mix a
replication into those counts.

## Files

- `policy.py`: the eight observation-only policy variants and optional self-review.
- `run.py`: corpus preparation and game runner, with no online oracle calls.
- `analyze.py`: offline verification, labels and development-only selection.
- `server.py`: local unassisted play, no solver.
- `build_report.py`: report and replay export from verified summaries.
- `records/`: exact requests/responses, trajectories, manifests and usage CSVs.
