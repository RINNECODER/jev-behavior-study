"""Build the Snake findings from verified, immutable episode records."""
import json
from pathlib import Path
from .build_demo import ROOT,MAIN,ENDURANCE,PILOT
from .engine import LEVELS
NAMES={'jev_direct':'Jev direct','jev_guarded':'Jev guarded','baseline':'Pathfinding baseline'}

def main():
    result=json.loads((MAIN/'analysis.json').read_text());extra=json.loads((ENDURANCE/'analysis.json').read_text())
    metrics={(m['level'],m['controller']):m for m in result['metrics']}
    table=['| Difficulty | Direct: mean / best / target successes | Guarded: mean / best / target successes | Baseline: mean / best / target successes |','|---|---:|---:|---:|']
    for level in LEVELS:
        values=[]
        for profile in NAMES:
            m=metrics[level,profile];values.append(f"{m['mean_food']:.2f} / {m['best_food']} / {m['target_successes']}/{m['episodes']}")
        table.append('| '+LEVELS[level]['label']+' | '+' | '.join(values)+' |')
    tokens=['| Difficulty / profile | Successful API calls | Mean input / call | Mean output / call | Median latency | P95 latency | Forced safe moves |','|---|---:|---:|---:|---:|---:|---:|']
    for level in LEVELS:
        for profile in ['jev_direct','jev_guarded']:
            m=metrics[level,profile]
            tokens.append(f"| {LEVELS[level]['label']} / {NAMES[profile]} | {m['model_calls']} | {m['mean_input_tokens_per_call']:.2f} | {m['mean_output_tokens_per_call']:.2f} | {m['median_latency_ms']:.0f} ms | {m['p95_latency_ms']:.0f} ms | {m['forced_moves']} |")
    endurance=['| Selected board | Guarded Jev food / moves | Baseline food / moves |','|---|---:|---:|']
    for level,seed in [('open',103),('open',104),('classic',104)]:
        a=json.loads((ENDURANCE/f'{level}-jev_guarded-{seed}.json').read_text());b=json.loads((ENDURANCE/f'{level}-baseline-{seed}.json').read_text())
        endurance.append(f'| {LEVELS[level]["label"]}, seed {seed} | {a["score"]} / {a["moves"]} | {b["score"]} / {b["moves"]} |')
    report=f'''# Jev plays Snake: what actually happened

[Open the replay demo](https://rinnecoder.github.io/jev-behavior-study/snake_demo/web/) ·
[Protocol](PROTOCOL.md) · [Run live locally](README.md)

**Best observed: six foods with direct Jev, eight with guarded Jev.** Those are
selected observed scores under the tested configurations, not estimates of Jev's
maximum possible skill. The deterministic baseline substantially outperformed
both Jev profiles in the main benchmark.

The study collected **96 main games**, a separate **three-game pilot**, and
**six selected endurance games** on September 17, 2026 UTC. Main games comprise
64 Jev-profile episodes and 32 deterministic baseline episodes. All valid API
responses returned `jev-1.13.0`. There were {result['model_calls']:,} successful
main-run API calls and one HTTP-error interruption. No automatic retry or
replacement was performed.

## Watch it

The browser demo includes all main and endurance games. Select a difficulty,
controller and seed; play, pause, step, scrub or download the replay. Each model
move displays its returned choice probabilities, confidence, latency and input/
output tokens. Forced safe moves and baseline actions are labeled as code,
with no fabricated model responses. The best-run selector explicitly selects a
high-scoring example, not a typical game. Endurance games have different caps
and are labeled in the run selector and notes.

The public site replays saved observations. Local live mode calls Jev through a
Python server and uses the same engine and controllers. Credentials remain on
the server; the static site does not contain a key or send paid API requests.
The game is visually rendered from coordinates. **Jev receives JSON state, not
screenshots**, so this is not a vision capability test.

## What each controller does

**Direct Jev** receives the board, body coordinates in head-to-tail order, food,
heading, obstacles, wrap rule, score and termination limits. It chooses from
left/straight/right. Each option describes the resulting absolute destination.
This coordinate transformation is common to both Jev profiles; no pathfinding
hints or future route are supplied.

**Guarded Jev** receives the same information, but code removes immediately
fatal choices. When only one safe choice remains, code takes it without a model
call. If none remains, a deterministic terminal move records a collision. This
is explicit algorithmic assistance: guarded performance must not be attributed
entirely to Jev. There were **152 forced safe moves** in the main run. All six
guarded collision endings occurred after no safe move remained; the guard did
not guarantee avoidance of future traps.

**The baseline** uses breadth-first distance to food among currently legal moves,
with a fixed tie break. It treats current body occupancy as blocked for route
selection. It is a simple deterministic comparator, not an optimal Snake solver;
it can trap itself. It makes no API calls.

Choice order rotates deterministically by seed plus move count. The Jev prompt
was fixed before the pilot and not tuned after seeing scores. Four episodes ran
concurrently. A saved main-run schedule shuffles episodes across controllers and
levels; within each game actions are necessarily sequential.

## Difficulty and scoring

Every board is 12×12. Open wraps at boundaries; Classic has solid edges. Obstacles
adds 12 blocked cells, Dense adds 24. Terrain generation preserves connectivity
and excludes the initial body and first forward cell. The levels are intended
challenge variants, not an assumption that every score must decline monotonically.

Main episodes stop at eight foods, 200 moves, a collision, or 50 consecutive
moves without food. Reaching eight is a **capped task success**, not winning all
of Snake. The same eight seeds, 101–108, are used for every controller/level.
Controllers share their initial board for each level/seed, but subsequent food
placement can diverge because food is sampled from currently free cells.

Each cell below shows **mean food / best food / eight-food successes** over eight
attempted episodes. Main averages never include pilot or endurance games.

{chr(10).join(table)}

The Classic/direct cell includes one interrupted game that had collected two
foods before an HTTP error. Its 3.38 mean is observed food over all eight attempts;
over the seven completed games the mean is 3.57. Its zero target successes
should not be interpreted as eight observed gameplay failures: one outcome is
censored by the API interruption. The error record preserves its type and exact
board state, but not the HTTP status/body; the precise provider failure cause
and failed-request token usage are unknown.

Across levels, direct Jev reached the target in **0/32 attempts**, guarded Jev
in **3/32**, and the baseline in **27/32**. Eight seeds per cell is a small,
synthetic sample. These totals are not general-purpose model win rates.

## What ended the games?

Among the 64 main Jev-profile games:

- **40** reached the 50-move no-food limit.
- **20** ended in collisions, including six guarded games with no safe next move.
- **3** reached eight foods.
- **1** was interrupted by an HTTP error.

Avoiding an immediately fatal move did not ensure progress toward food or prevent
longer-term traps. The wrapping Open level was not automatically easier for Jev:
direct Jev averaged 1.75 there versus 3.38 observed on Classic. We did not isolate
whether wrap reasoning, particular food sequences, prompt framing or other
factors caused that contrast.

Guarding improved the mean on Open, Classic and Dense, but not Obstacles (1.50
versus direct's 1.75). Seeds were paired only at initialization, so this is an
observed system-level contrast, not identical per-state model comparisons.

## Selected endurance: testing beyond the eight-food cap

After observing the main run, we selected its three guarded target-reaching
boards: Open seeds 103/104 and Classic seed 104. We ran fresh guarded decisions
and paired baseline games with a **24-food target and 600-move cap**, retaining
the 50-move no-food rule. These six runs are adaptive selected follow-ups and
are excluded from all main averages.

{chr(10).join(endurance)}

All three fresh Jev games stopped at the no-food limit, collecting one, two or
four foods; none exceeded the earlier eight-food score. The baseline reached 24
on two boards and collided at 12 on the third. This does not prove Jev cannot
collect nine foods. The higher limits are part of the supplied state, fresh
responses can differ, and later food depends on the trajectory. These are not
replays of identical requests and not evidence of a uniquely identified failure
mechanism. The best observed guarded score remains eight, with substantial
variation across configurations and calls.

## Latency and tokens per decision

The board advances only after the decision returns. There is **no fixed-rate
real-time deadline** and no skipped physics ticks while the network is busy.
This measures gameplay decisions independently of network response time. Replay
speed controls viewing speed; it is not a performance claim. Recorded-timing
playback approximately follows saved call latencies, with a minimum display
interval for code-only moves.

There is exactly one question per model request. Per-call token figures include
the provider-counted state, question schema and overhead. Baseline/forced moves
make no model request; their model usage is zero by construction, not an estimate
of failed-call usage. Wall-clock elapsed episodes include orchestration and
concurrent execution; do not infer model throughput from replay frame rate.

{chr(10).join(tokens)}

Latency is measured client-side around the HTTP request. The P95 shown uses the
sorted observation at index `floor(0.95 × n)` (capped at the final observation).
The median is around one-third of a second in this environment; this is not an
isolated vendor inference-only latency or a guarantee for another deployment.

[Exact main per-decision usage](records/{MAIN.name}/per_decision_usage.csv) ·
[Endurance usage](records/{ENDURANCE.name}/per_decision_usage.csv) ·
[Pilot usage](records/{PILOT.name}/per_decision_usage.csv)

The main run reported **{result['input_tokens']:,} input / {result['output_tokens']:,}
output tokens** on successful calls. The selected endurance run reported
**{extra['input_tokens']:,} input / {extra['output_tokens']:,} output tokens**.
These are accounting totals; use the CSVs for individual question costs.
Unknown billing for the interrupted request is not silently assigned zero.
Local interactive QA calls are outside these frozen study runs.

## Verification and reproducibility

[The analyzer](analyze.py) regenerates every initial board and replays every move,
checking before/after states, legal-action filtering, forced decisions, baseline
moves, payload hashes, raw response parsing, model version, option probability
sets, score/call/token totals and completion counts. Nine rule/controller unit
tests separately cover growth, walls, wrapping, self-collision, vacating tails,
termination and determinism. Browser QA covers replay controls, difficulty and
controller selection, best-run selection, and an actual live Jev move.

```bash
python -m unittest -v snake_demo.test_snake
python -m snake_demo.build_demo
python -m snake_demo.build_report
python -m snake_demo.server
```

The first three commands make no API requests. The server serves the demo at
`http://127.0.0.1:8765`; new paid calls occur only when you start a live Jev game.
For another full benchmark, set `TYPESAFE_API_KEY` in your environment or ignored
local `.env`, then run `python -m snake_demo.benchmark --plan-only` to inspect
scope and `python -m snake_demo.benchmark` to execute it. New evidence receives
new timestamped directories. Replay exports are rebuildable from raw records.

Evidence directories: [pilot](records/{PILOT.name}/),
[main](records/{MAIN.name}/), [endurance](records/{ENDURANCE.name}/).
Each game has a summary `.json` and chronological `.jsonl` records. The main
manifest fixes jobs, model, rules and limits before execution. The protocol
separately discloses the adaptive endurance selection. No successful clip replaces
failed games in the dataset.

## Limits of the conclusion

This evaluates two particular structured-state prompts/controllers, one fixed
board size, eight main seeds per level, and a small selected follow-up. It is
not a search over all possible Jev prompts, representations, memory systems or
planning tools. A different observation format or external planner could change
results; an assisted system would need its assistance measured explicitly.

Jev can control the environment and sometimes collect multiple foods, but it
was not consistently competent under these tested setups. A simple non-AI
baseline performed much better. The honest answer to “what is the best it can
do?” is **six foods direct and eight guarded observed here**, with successful
examples available to inspect and no claim that these are absolute limits.
'''
    (ROOT/'SNAKE_REPORT.md').write_text(report)
    print('Wrote snake_demo/SNAKE_REPORT.md')
if __name__=='__main__':main()
