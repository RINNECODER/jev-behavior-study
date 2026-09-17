"""Render the research report from verified stage summaries; no API requests."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
R=ROOT/'records'
def read(path):return json.loads(path.read_text())
def pct(k,n):return f'{100*k/n:.1f}%' if n else 'n/a'
def interval(bounds):return '–'.join(f'{100*x:.1f}%' for x in bounds)

def main():
 d=read(R/'diagnosis-v1/analysis.json');g=read(R/'gameplay-v1/analysis.json');old=read(R/'old-classic-summary.json');stress=read(R/'stress-v1/analysis.json')['oracle'];long=read(R/'long-planner-v1/analysis.json')['oracle'];dev=read(R/'long-v2-development/analysis.json');hold=read(R/'long-v2-holdout/analysis.json')
 variants=['original','compact','absolute','local','exact'];table=[]
 for v in variants:
  a=d['metrics']['development/ablation/'+v];b=d['metrics']['holdout/ablation/'+v]
  table.append(f"| {v} | {a['correct']['count']}/60 | {b['correct']['count']}/60 | {interval(b['correct']['wilson_95'])} | {b['safe']['count']}/60 |")
 games=[]
 for p in ['unassisted','assisted','verified','oracle']:
  x=g[p];s=x['stats'];n=s.get('valid_calls',0)
  games.append(f"| {p} | {x['successes']}/{x['episodes']} | {s.get('model_shortest',0)}/{n}"+(f" ({pct(s.get('model_shortest',0),n)})" if n else ' (no model)')+f" | {x['shortest_food_segments']}/{x['food_segments']} | {s.get('overrides',0)} |")
 calls=d['total']['valid']+sum(x['stats'].get('valid_calls',0) for x in g.values());inp=d['total']['input_tokens']+sum(x['stats'].get('input_tokens',0) for x in g.values());out=d['total']['output_tokens']+sum(x['stats'].get('output_tokens',0) for x in g.values())
 text=f'''# Classic Snake: diagnosing Jev, improving the controller, and testing the limits

[Interactive experiment](https://rinnecoder.github.io/jev-behavior-study/snake_demo/web/classic.html) · [Protocol](PROTOCOL.md) · [Adaptive amendments](AMENDMENTS.md) · [Run/reproduce](README.md)

## Result and scope

**We obtained perfect observed short-task performance with explicit planner assistance. We did not establish universally perfect Snake or independent optimal planning by Jev.**

On 16 fresh Classic seeds, Jev supplied with exact route lengths reached the eight-food target in **16/16 games**, choosing a shortest legal move in **1,061/1,061 decisions**. A separate verifier-backed profile also achieved 16/16 and 1,061/1,061, with **zero overrides**. The original prompt achieved **0/16 games** and **967/1,515 shortest decisions (63.8%)**. These game profiles were selected using development states before the held-out gameplay schedule was executed.

The successful controller asks Jev to choose among code-computed route lengths. Code performs the hard search. Zero overrides does not mean zero assistance: every assisted proposal had access to a solved route comparison. The code-only planner itself completed 16/16 paired short games and a separate **100/100** short-game stress test without using Jev.

For 16/16 observed game successes, the descriptive Wilson 95% interval is **{interval(g['assisted']['success_wilson_95'])}**. The 1,061 moves are dependent observations within those games, not 1,061 independent full-game trials. No finite sample proves universal 100%.

Longer games exposed planner limits. The original exact planner completed **{long['successes']}/16** code-only 24-food games. A bounded-search repair improved that to **{dev['successes']}/16** on the same development seeds, and completed **{hold['successes']}/16** on new held-out long-game seeds. The remaining failures are retained. The predeclared gate for a new long-game Jev test was not met, so that test was not run. Long-game code results must not be described as Jev results.

## Scientific question and experimental units

The user's goal was reliable, efficient Classic Snake. “Accuracy” has several distinct meanings:

1. **Immediate legality:** avoid the wall or current body on the next move, accounting for the tail vacating.
2. **Shortest-action accuracy:** select a first action belonging to any minimum-length legal path to the currently visible food, with the whole body moving at every step.
3. **Food-segment efficiency:** compare actual moves from a segment's start to its food with the exact minimum at that start. Only completed food segments enter this metric; stalled/uncompleted segments remain visible through episode failures and action accuracy.
4. **Task completion:** reach eight foods within 200 moves, with a 50-move no-food limit. Longer tests separately use 24 foods and 600 moves.

The board is always 12×12 with solid edges, no obstacles, initial length three and no reverse moves. Eight-food success is not filling the 144-cell board. Minimizing moves to current food is not globally minimizing moves over future food. Food is drawn from free cells; controllers starting from the same seed can receive different later food because they occupy different cells. There is no future-food access in the solver or prompt.

## Prior evidence: what was actually wrong?

An offline audit of the original Classic games evaluated 1,617 saved model decisions without new API calls. All had resolved exact shortest-action labels:

| Original profile | Legal decisions | Shortest decisions | Returned choice in probability argmax |
|---|---:|---:|---:|
| Direct | {old['jev_direct']['legal']}/616 | {old['jev_direct']['shortest']}/616 | 616/616 |
| Guarded | {old['jev_guarded']['legal']}/1001 | {old['jev_guarded']['shortest']}/1001 | 1001/1001 |

This supports a behavioral description: most moves were legal, but many did not follow a shortest route to food. It does not identify the model's internal reasoning mechanism. The new held-out original-prompt games repeated that pattern: 1,507/1,515 legal moves, but only 967/1,515 shortest moves. Thirteen state recurrences were observed across those games; a recurrence is evidence of repeated board configuration, not a diagnosis of the model's internal memory.

One concrete held-out example is [holdout-012, original](records/diagnosis-v1/holdout-012-original.json). The head is at (5,6), facing west, with food at (5,9). The exact legal route lengths for left/straight/right are 3/5/7. Jev chose straight, adding avoidable distance. In [the exact-facts version](records/diagnosis-v1/holdout-012-exact.json), the computed route comparison is supplied explicitly. Body positions and the complete request/response are preserved in each record.

## Design, hypotheses, and observations

The initial protocol and 120-state corpus were committed before new calls (`454b2b6`). Development contains 20 states each from previous direct games, previous baseline games and new random-legal trajectories. Holdout contains 30 baseline and 30 random-legal states from new seeds 301–320. State fingerprints are unique across the two partitions. States are correlated within trajectories; neither partition is a representative distribution of all possible Snake positions.

All 600 main fixed-state calls use exactly the same 120 states crossed with five frozen variants. The corpus is selected for resolved, food-reachable oracle states; unresolved states are not silently scored correct. Choice ordering rotates by state index, with the same ordering for paired variants.

| Variant | Development shortest | Holdout shortest | Holdout descriptive Wilson 95% | Holdout legal |
|---|---:|---:|---:|---:|
'''+ '\n'.join(table)+f'''

- **H1 — simplify state/instructions:** compact did not beat original on development (41 versus 44), although it scored 45 versus 41 on holdout. There is no consistent improvement establishing this as the fix. This ablation changes both state and wording; it cannot isolate their separate causal contributions.
- **H2 — use absolute directions:** absolute scored 40/60 development and 48/60 holdout. This mixed pattern does not establish that relative-turn naming was the main failure mechanism.
- **H3 — expose local facts:** immediate safety plus computed Manhattan distance scored 57/60 in both partitions. That is a useful observed improvement, but the added arithmetic/safety work is code assistance. Manhattan distance does not certify routes around the moving body.
- **H4 — expose exact route costs:** 60/60 in each partition. Jev reliably selected minima on this tested set. This tests numerical selection from a solved problem; it is not evidence Jev independently discovered the routes.
- **H5 — order/repetition sensitivity:** 12 fixed development states × all six option orders × two repeats produced 144 valid calls. Seven states had more than one returned action across their calls. Identical payload pairs disagreed **8/72** times, so changes cannot all be attributed to option order. The experiment does not isolate whether backend nondeterminism, model sampling or infrastructure caused identical-input differences. More than one action may be equally optimal.
- **H6 — atomic questions:** 90 standalone safety checks were **89/90** correct; 90 standalone Manhattan-progress checks were **70/90** correct. Narrowing a question did not make coordinate/distance judgments perfect. These are different tasks from choosing a route, so their percentages are not interchangeable measures of “intelligence.”
- **H7 — verify model proposals:** the exact-facts profile and its verifier-backed counterpart both passed all 16 short games. No proposal required an override, so this sample provides no measured incremental performance benefit from the verifier. The verifier remains a code-enforced local constraint, not a universal survival guarantee.

Paired improved/worsened counts are available in [analysis.json](records/diagnosis-v1/analysis.json). The study does not claim corrected statistical significance across these exploratory comparisons. Selection used development performance, not the better-looking holdout result: **original** was retained as the unassisted profile and **exact** as assisted.

## Full-game validation on unseen seeds

Selection and the shuffled 64-game schedule were committed before execution (`885e30d`). Seeds 1001–1016 were new. There are 16 games per profile. Episodes ran with four workers, but each episode's turns were sequential; there was no automatic retry or replacement of failed games.

| Profile | Eight-food successes | Shortest model proposals | Shortest completed food segments | Overrides |
|---|---:|---:|---:|---:|
'''+ '\n'.join(games)+f'''

The original-prompt endings were {json.dumps(g['unassisted']['endings'],sort_keys=True)}. Both assisted profiles and code-only planner ended at the target in every paired game. The two assisted profiles can share successful trajectories because their inputs and decisions can coincide; they are not independent proof replications across distinct task distributions.

All executed moves in the two assisted profiles were shortest, and all their completed food segments used the minimum number of moves from that segment's actual initial state. Ties between shortest routes are valid. Total episode lengths can differ between controllers without contradicting this local optimality claim, because tie choices can change subsequent body occupancy and food.

## Why the planner needed its own experiment

The first solver ran exact A* separately after each candidate turn. A* state includes the complete ordered body and heading. The Manhattan heuristic is admissible; the search simulates tail movement and stops upon reaching the current food. Each search has a 100,000-expanded-node cap. Budget exhaustion is **unknown**, not a proof of unreachable food.

In the 24-food development extension, seed 4001 stopped at 15 foods. Re-examination found a solved six-move route starting right, but the search for left exhausted its budget. The controller required all candidate costs resolved and therefore stopped. This was a concrete computational limitation in our harness, not a model error and not proof the snake was doomed.

The separately frozen v2 repair solves the optimum D once, then checks each first action only for paths of length at most D. Failure of that bounded search yields a lower bound D+1; it does not mean a collision or an unreachable target. This removes unnecessary work on worse alternatives. V2 matched v1's optimal-action sets on all 120 frozen states before transfer testing.

| Code-only test | Target | Completed | Interpretation |
|---|---:|---:|---|
| Original exact planner, fresh short seeds 2001–2100 | 8 | {stress['successes']}/100 | Short-task code stress; no model calls |
| Original exact planner, long seeds 4001–4016 | 24 | {long['successes']}/16 | Adaptive extension; {16-long['successes']} planner stoppages |
| Bounded v2, same long seeds | 24 | {dev['successes']}/16 | Development repair retest, not fresh confirmation |
| Bounded v2, fresh long seeds 5001–5016 | 24 | {hold['successes']}/16 | Unseen long-game transfer; remaining unknowns retained |

The remaining v2 outcomes are {json.dumps(hold['totals'],sort_keys=True)}. A further development-only probe changed the A* equal-priority tie break to prefer deeper states on the failed seed-5006 state. It also exhausted 100,000 nodes; its failed result is retained in [the probe record](records/deep-tie-development-probe.json). No revised model controller was promoted from this probe. A root search can still exceed the budget. We have not proved that these positions are unwinnable. Increasing the search budget, choosing routes with future survivability constraints, or using a Hamiltonian-cycle strategy would change the system. A cycle-based controller could favor survival while taking longer routes; it would not meet a blanket claim of shortest-path efficiency.

The conditional new Jev long-game test required the code-only planner to pass every fresh long game. It failed that gate. We therefore did not spend model calls to obscure an already demonstrated planner limit. The requested universal end state remains **unproven and unmet**; the eight-food configuration has a verified perfect observed result.

## Confidence, probability, and tokens

Every new call contains exactly one question. Each record and CSV preserves the provider's exact input and output token count for that question's request, including state/schema overhead. There is no allocation of a multi-question request's tokens by division. Baseline moves make no API request. Planner runtime is separate from client-measured API latency.

The new study contains **{calls:,} successful model calls**, **{inp:,} reported input tokens**, and **{out:,} reported output tokens**. This comprises 924 fixed-state/atomic/order calls plus the closed-loop model calls; code-only stress games and the old-record audit add no model usage. Live browser QA is logged separately and excluded. No new study API failures occurred.

- [Fixed-state tokens per question](records/diagnosis-v1/per_question.csv)
- [Full-game tokens per question](records/gameplay-v1/per_question.csv)
- [Exact payloads/responses and corpus](records/diagnosis-v1/)
- [Full-game transitions](records/gameplay-v1/)

All 924 diagnostic returned choices belonged to the maximum-probability set. Probability ties are retained; a returned choice need not be the first key a client gets from an arbitrary argmax tie break. This batch does not support a choice-versus-argmax bug explanation. Confidence is a summary of the returned distribution, not a route certificate; TypeSafe documents it as derived from those probabilities. [TypeSafe confidence documentation](https://docs.typesafe.ai/confidence)

TypeSafe recommends narrow questions and combining independent judgments in code. That motivated an atomic-question test, but the vendor recommendation is not evidence that a particular decomposition must succeed. The measured progress-question errors remain part of this study. [TypeSafe introduction](https://docs.typesafe.ai/introduction)

## Verification, reproducibility, and caveats

The first two commits freeze the initial test and selected gameplay schedule; later dated amendments preserve the adaptive longer-game tests and search repair. The original failed games and all subsequent failures remain available. No successful rerun replaces a failed run. Development and holdout selection, code-assisted features and conditional stopping are explicit.

Six oracle/controller tests cover independent BFS comparisons on small boards, dynamic body positions and candidate first turns, vacating tails, walls, one-move food, and budget-unknown handling. The original nine engine/controller tests remain passing. Exact search witnesses are replayed with the actual engine. All successful v1/v2 move certificates and complete before/after trajectories are verified; v2 terminal unknown records are checked structurally and retained as unknown, not rerun to make them pass.

The new viewer provides the 64 held-out game replays, the original model proposal, executed action, exact route costs, planner runtime and per-question usage. Live mode uses the same eight-food v1 controller on localhost and keeps credentials server-side. A browser QA live call is outside experiment totals. The repaired v2 long-game code is a separate research component, not silently substituted into those published replays.

Limitations include one model version, synthetic seeded environments, a limited prompt family, correlated trajectory states, assisted answer leakage by design, adaptive follow-ups, no weight training, no pixel/vision input, no real-time deadline, finite search budgets, and no global multi-food optimum. Changing prompts or harnesses does not train or permanently update Jev's model weights.

## Practical conclusion

For the tested short Classic task, use **exact route facts plus a verifier** if a constrained Jev-based controller is desired. If the objective is simply to solve these boards, the code-only planner achieves the result without Jev calls. Prompt simplification, absolute direction labels and atomic wording alone did not establish perfect behavior.

The experiment demonstrates a useful boundary: Jev was reliable at selecting a supplied optimum here, but unreliable at deriving consistently efficient routes from raw coordinates. Further work on long-game safety and search complexity belongs to the planner/controller design as well as the model interface. There is no supported basis for claiming universally perfect, globally most-efficient Classic Snake.
'''
 (ROOT/'REPORT.md').write_text(text)
 print('Wrote report:',calls,'calls',inp,'input',out,'output')
if __name__=='__main__':main()
