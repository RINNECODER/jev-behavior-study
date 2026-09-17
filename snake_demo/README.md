# Jev / Snake Lab

[Watch the demo](https://rinnecoder.github.io/jev-behavior-study/snake_demo/web/) ·
[Read the results](SNAKE_REPORT.md) · [Protocol](PROTOCOL.md)

A replayable Snake experiment with four difficulty levels, direct and guarded
Jev controllers, a deterministic baseline, and exact per-decision evidence.
The static demo includes all 96 main games and six separately labeled endurance
games. It uses no API key. The three pilot games remain in the raw evidence.

## Run locally

Python 3.10+, standard library only. From the repository root:

```bash
python -m snake_demo.server
```

Open http://127.0.0.1:8765. Replays and the live deterministic baseline work without
a key. For live Jev, set `TYPESAFE_API_KEY` in your shell or the ignored root
`.env` before starting the server. It binds to localhost only. The API key never
enters browser JavaScript or the public replay data. Live games are logged under
ignored `snake_demo/records/live-*/` directories, outside published study totals.
The **Live** tab makes paid model calls when a Jev controller is selected.

Controls: select difficulty, controller and seed; play/pause, advance one move,
seek any frame, adjust playback speed, select the best recorded game, or download
a replay. Share the URL after selecting a recorded game. Endurance games have
higher caps and are labeled; the results table always uses the main benchmark.

## Reproduce offline

```bash
python -m unittest -v snake_demo.test_snake
python -m snake_demo.build_demo
python -m snake_demo.build_report
```

To verify another saved run without changing the viewer dataset:

```bash
python -m snake_demo.analyze snake_demo/records/<run-directory> --no-export
```

## Run a fresh paid study

```bash
python -m snake_demo.benchmark --plan-only
python -m snake_demo.benchmark --pilot
python -m snake_demo.benchmark
```

The main benchmark has 96 episodes, with at most 12,800 API requests before
termination/forced-move reductions. It does not retry errors. The existing
`endurance.py` is specifically the disclosed follow-up to the published main
study, not a general automatic optimizer.

## Files

- `engine.py`: deterministic game rules and baseline.
- `controller.py`: pinned Jev request format and explicit safety filter.
- `benchmark.py`, `endurance.py`: recorded experiments.
- `analyze.py`: replay verification, usage CSVs and viewer export.
- `server.py`: localhost static/live server.
- `web/`: dependency-free browser UI and generated replay data.
- `records/`: raw payloads, responses, state transitions and summaries.

No vision or screenshot input is used. Games wait for each decision; replay
speed is separate from latency. See the report before treating a best replay
as representative performance.
