# Jev / City lab

A real 3D driving sandbox for comparing **real-time** and **paused** Jev decisions on the same city and traffic seed.

[Open the demo](https://rinnecoder.github.io/jev-behavior-study/city_demo/) · [Findings](REPORT.md) · [Protocol](PROTOCOL.md) · [QA](QA.md)

The public page plays recorded Jev runs and supports manual keyboard driving. Live Jev runs use the local server. All three challenges are available: reach a destination, explore the city, and complete a delivery route. Follow/map cameras, replay scrubbing, a timing comparison table, exact tokens per question, run export and image capture are included.

| Technique | What Jev receives | What executes its decision |
|---|---|---|
| Direct controls | Structured vehicle, road, signal and nearby-traffic state | Selected steering, throttle and brake; no safety correction |
| Assisted maneuvers | The same structured state | A disclosed lane/turn/speed controller |
| Native vision | Not verified for jev-1.13.0 | Unavailable; screenshots are not silently treated as text |
| Manual | The human sees the city | WASD / arrow keys; not a model result |

Real time holds the previous control while the city continues moving during API calls. Paused mode waits with everything frozen, then advances 0.6 simulated seconds. Both clocks use the same 50ms physics engine. Replay plays simulation time and omits API waits; it makes no model calls.

## Run locally

From the repository root:

```bash
# Set TYPESAFE_API_KEY in your environment or the ignored root .env.
python3 city_demo/server.py
```

Open **http://127.0.0.1:8768/**. Select the driver, challenge, clock and seed, then Start drive. Keys stay server-side. The server binds only to localhost. Each live model decision makes two paid API calls, one question per call; a run stops at 160 decisions, first collision, completion, 90 simulated seconds or API error. Stop drive prevents future calls; a request already sent may finish and is logged without applying a late action. Hiding the browser tab terminates the live episode explicitly.

The frontend needs WebGL. It uses vendored Three.js 0.170.0 ([MIT license](vendor/THREE-LICENSE.txt)); no npm install or third-party CDN is needed. Python uses only the standard library. Keyboard manual driving requires a keyboard; the mobile interface supports watching and configuring Jev runs.

## Reproduce and inspect

```bash
node --test --test-isolation=none city_demo/test.mjs
node city_demo/validate.mjs
python3 city_demo/analyze.py
python3 city_demo/build_report.py
# Optional: new paid experiment, with the local server running:
node city_demo/benchmark.mjs city_demo/records/my-new-pilot
```

Node 20+ supports the application modules; Node 22+ is recommended for the displayed test-runner flag (alternatively `node city_demo/test.mjs`). The benchmark refuses an existing output directory and checks the proxy before starting. It records a source manifest before its first model call. To analyze additional folders, use `analyze(folder)` in analyze.py; the default command rebuilds the two published pilots.

- [Corrected pilot v2](records/pilot-v2/analysis.json): primary descriptive findings; one episode per condition.
- [Per-question CSV](records/pilot-v2/per-question.csv): exact individual input/output token counts, not divided totals.
- [Original pilot v1](records/pilot-v1/analysis.json): retained because its traffic-following flaw confounded interpretation.
- [Source snapshot for v1](records/pilot-v1/source/): reproduces the original environment.
- Episode JSONs contain raw provider responses, exact payloads, decisions, application timestamps, frames, terminal state and events. Authentication headers are never stored.

Live proxy call logs are ignored under `records/live-*`. The benchmark artifacts are deliberately versioned. Everything for this new demo is isolated in `city_demo`; no parent workspace is added to the repository.
