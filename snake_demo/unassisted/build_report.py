"""Build the unassisted report and replay data from verified results."""
from collections import defaultdict,Counter
import csv
import json
from pathlib import Path
import statistics
from .policy import VARIANTS
ROOT=Path(__file__).resolve().parent
R=ROOT/'records'
NAMES={'original':'Original','priority':'Explicit priorities','narrative':'Prose description','ascii':'ASCII grid','egocentric':'Head-relative coordinates','history':'Four-move history','absolute':'Absolute directions','review':'Two-call self-review'}
def read(p):return json.loads(p.read_text())
def pct(k,n):return f'{100*k/n:.1f}%' if n else 'n/a'
def bounds(b):return '–'.join(f'{100*x:.1f}%' for x in b)

def main():
 screen=read(R/'screen-v1/analysis.json');dev=read(R/'development-v1/analysis.json');test=read(R/'holdout-v1/analysis.json');metrics=test['metrics']
 screen_table=[]
 for v in VARIANTS:
  m=screen['metrics'][v];screen_table.append(f"| {NAMES[v]} | {m['shortest']}/80 | {m['legal']}/80 | {m['calls']} |")
 dev_table=[]
 for v in ['original']+screen['selected']:
  m=dev['metrics'][v];dev_table.append(f"| {NAMES[v]} | {m['successes']}/4 | {m['mean_food']:.2f} | {m['stats']['shortest']}/{m['stats']['valid_decisions']} |")
 final_table=[];cost_table=[];usage=[]
 for stage in ['screen-v1','development-v1','holdout-v1']:
  with (R/stage/'per_question.csv').open() as f:usage.extend({'study_stage':stage,**x} for x in csv.DictReader(f))
 for v in ['original']+dev['selected']:
  m=metrics[v];s=m['stats'];final_table.append(f"| {NAMES[v]} | {m['successes']}/16 | {bounds(m['success_wilson_95'])} | {m['mean_food']:.2f} | {s['shortest']}/{s['valid_decisions']} ({pct(s['shortest'],s['valid_decisions'])}) | {s['legal']}/{s['valid_decisions']} |")
  calls=[x for x in usage if x['study_stage']=='holdout-v1' and x['variant']==v and x['valid']=='True']
  cost_table.append(f"| {NAMES[v]} | {len(calls)} | {sum(int(c['input_tokens']) for c in calls)/len(calls):.1f} | {sum(int(c['output_tokens']) for c in calls)/len(calls):.1f} | {statistics.median(float(c['latency_ms']) for c in calls):.0f} ms |")
 successes=sum(x['valid']=='True' for x in usage);failures=len(usage)-successes;inp=sum(int(x['input_tokens']) for x in usage if x['input_tokens']);out=sum(int(x['output_tokens']) for x in usage if x['output_tokens'])
 error_statuses=dict(Counter(x['http_status'] or 'unknown' for x in usage if x['valid']!='True'))
 by=defaultdict(dict)
 for row in read(R/'screen-v1/scored_decisions.json'):by[row['state_id']][row['variant']]=row['score']['shortest']
 paired=[]
 for a,b in [('original','priority'),('priority','narrative'),('priority','ascii'),('priority','history'),('priority','absolute'),('priority','egocentric')]:
  paired.append(f"| {NAMES[a]} → {NAMES[b]} | {sum(not x[a] and x[b] for x in by.values())} | {sum(x[a] and not x[b] for x in by.values())} |")
 final_pair=[];completed_pair=[]
 for v,p in test['paired_vs_original'].items():
  c=p['both_completed'];completed_pair.append(f"{NAMES[v]}: {c['food_wins']} wins, {c['food_ties']} ties, {c['food_losses']} losses across {c['n']} pairs")
  final_pair.append(f"| {NAMES[v]} | {p['food_wins']} | {p['food_ties']} | {p['food_losses']} | {p['completion_wins']} | {p['completion_losses']} |")
 endings=[];completed_only=[]
 for v,m in metrics.items():
  completed_only.append(f"{NAMES[v]}: {m['successes']}/{m['completed_games']} completed games, API-interrupted games: {m['api_interrupted_games']}")
  endings.append(f"- **{NAMES[v]}:** {', '.join(str(n)+' '+k.replace('_',' ') for k,n in m['endings'].items())}; {m['stats']['repeated_states']} repeated full board states; {m['shortest_food_segments']}/{m['scored_food_segments']} scored completed food segments used the shortest route.")
 best=max(dev['selected'],key=lambda v:(metrics[v]['successes'],metrics[v]['total_food'],-VARIANTS.index(v)))
 # Default viewer follows the DEVELOPMENT recommendation, not a post-hoc test selection.
 preferred=dev['selected'][0]
 control=metrics['original'];prose=metrics.get('narrative');absolute=metrics.get('absolute')
 text=f'''# Improving unassisted Jev at Classic Snake

[Interactive held-out results](https://rinnecoder.github.io/jev-behavior-study/snake_demo/web/unassisted.html) · [Protocol](PROTOCOL.md) · [Reproduce / play live](README.md)

## What changed, and what the evidence says

This study supplies **no route answers, safe-move labels, distances, ranked options, action masks, corrections or fallback moves**. Jev's final choice executes unchanged. The exact solver is used only after calls/games finish to score them. No oracle failure can interrupt or change an agent's game.

The best final observed completion result among the preselected candidates was **{NAMES[best]}: {metrics[best]['successes']}/16 games**, compared with **{control['successes']}/16** for the contemporaneous original-prompt control. That is a finite result for these seeds and the eight-food cap, not a universal accuracy guarantee. The complete comparison, including lower-scoring and failed games, is below.

The strongest DEVELOPMENT configuration was a plain-language description of the board plus explicit priorities. It passed 4/4 development games and was frozen before final testing. The second finalist used absolute direction labels. Head-relative coordinates were excellent on individual development states (78/80 shortest moves) but collided in two of four complete games, so they were rejected by the predeclared selection rule.

**This differs from the earlier assisted result.** The earlier controller asked Jev to select from exact route lengths computed by code. Here, no such lengths enter any model request. A prose description restates observed coordinates; it does not say where to go. Absolute action descriptions specify what a command means, not whether it is safe or good. The rejected head-relative variant does perform a declared geometric rotation/translation, but no route search or action-quality calculation.

## Primary held-out results

Classic 12×12 board, solid edges, initial body length three, eight-food target, 200-move cap, 50-move no-food limit. Seeds 9101–9116 were reserved before final testing. There are 16 games per profile. No final prompt edits, seed replacements or retries were made after seeing these results.

| Policy | Eight-food successes | Descriptive Wilson 95% | Mean food | Shortest final moves | Legal final moves |
|---|---:|---:|---:|---:|---:|
'''+ '\n'.join(final_table)+f'''

A shortest move starts some minimum-length legal route to the **current** food with the tail moving. It is not a guarantee of survival after reaching that food or a globally optimal route across unknown future food. This test does not mean filling the whole board. Move observations within a game are correlated; the game interval must not be replaced with an apparently precise interval over thousands of dependent moves.

API interruptions are censored gameplay outcomes, not observed Snake losses. The table above counts successes per attempted game and reports food observed before interruption. Excluding interrupted games descriptively: **{'; '.join(completed_only)}**. Exclusion does not establish what the interrupted games would have done; their API costs, partial trajectories and unknown failed-call usage remain visible.

**Paired comparisons against the original prompt (observed food, including censored attempts):**

| Candidate | More food | Same food | Less food | Candidate-only target | Original-only target |
|---|---:|---:|---:|---:|---:|
'''+ '\n'.join(final_pair)+f'''

For pairs where BOTH games finished without API interruption, the observed food comparisons are **{'; '.join(completed_pair)}**. These exclusions are descriptive, not a substitute batch.

Pairing fixes each seed's initial board/food, not the entire future environment. Food spawns among currently unoccupied cells, so different bodies and routes can produce different later food positions from the same seed. New seeds also do not guarantee that every individual board position is novel; a small board can repeat configurations across games.

**Endings and efficiency:**

'''+ '\n'.join(endings)+f'''

Completed-food-segment efficiency excludes unfinished segments, which is why it is secondary to whole-game success and action accuracy. The number of unresolved offline shortest labels in final testing is **{sum(m['stats']['oracle_unknown'] for m in metrics.values())}**. Unknown labels cannot earn a correct score and never trigger a runtime fallback.

## Experimental sequence and hypotheses

### 1. Freeze candidates and screen on development states

The protocol, code and 80-state development corpus were committed before calls (`f742471`). The corpus is sampled without replacement from unique board configurations in the prior study's 16 unassisted games, seeds 1001–1016. Those previous games are explicitly repurposed as DEVELOPMENT data, not claimed to be a fresh holdout. Selection did not consult a solver or correctness labels. Four prior observations/actions are saved where available.

Eight variants were tested on every state, with common rotated option order. Review uses two calls; others use one. The 640 final decisions required 720 requests. Solver labels were produced afterward.

| Variant | Shortest final choices | Legal final choices | Model requests |
|---|---:|---:|---:|
'''+ '\n'.join(screen_table)+f'''

Paired changes on the same 80 states:

| Comparison | Wrong → shortest | Shortest → wrong |
|---|---:|---:|
'''+ '\n'.join(paired)+f'''

These comparisons are exploratory. No multiple-comparison-corrected significance or internal causal mechanism is claimed. State samples come from correlated old trajectories and may favor problems encountered by the old policy.

### 2. Validate screening winners in complete development games

The top three non-original variants were selected by shortest correct count per attempted screen decision, then legality, then fewer requests, then frozen order. This chose head-relative coordinates, prose and absolute directions. They were tested alongside original on seeds 8101–8104; the schedule was committed before execution (`7817f08`).

| Variant | Targets reached | Mean food | Shortest final moves |
|---|---:|---:|---:|
'''+ '\n'.join(dev_table)+f'''

Ranking on game successes, then food, then shortest-action fraction and cost selected **{', '.join(NAMES[v] for v in dev['selected'])}** for the final test. The final selection and schedule were committed before calls (`a08c979`). This is why the apparently strongest single-state policy was not automatically declared the winner.

### 3. Test once on unseen seeds

The two finalists and original were evaluated on seeds 9101–9116, giving 48 held-out games. The primary comparison is this contemporaneous control, not the older 0/16 original result. In fact, original had passed 2/4 development games here, illustrating why a favorable or unfavorable small seed set should not be treated as a universal capability estimate.

## Which hypotheses were supported?

- **Explicit priorities:** improved the development screen from 55/80 to 60/80. It also changes the observation from full metadata to compact fields, so the difference does not isolate goal wording alone. It did not rank high enough for a separate final-game test.
- **Prose instead of structured field lists:** 70/80 versus the otherwise comparable priority variant's 60/80, with ten paired improvements and no paired regressions in this screen; 4/4 development games. The final 16-game result above is the stronger test of whether this benefit transferred. An inference is that representation affects this model's use of coordinates; the experiment does not reveal its hidden computation.
- **ASCII grid:** 60/80, identical shortest-correct counts and paired correctness outcomes to priority. No demonstrated benefit from the extra grid on these states; this is a text grid, not a vision test.
- **Head-relative coordinates:** 78/80 shortest but only 79/80 legal screen choices, followed by 2/4 complete-game success. Both development failures were wall collisions. Normalizing geometry helped the measured route choice while failing to establish boundary reliability. This is an observed tradeoff, not proof all relative representations must fail.
- **Recent history:** 59/80 versus priority's 60/80 (one paired improvement, two regressions). No benefit established from adding four previous observations/actions in this design. Screen histories come from the old policy; self-generated history in a new policy may behave differently and was not separately validated in full games because it failed selection.
- **Absolute direction keys:** 61/80, then 3/4 development games. It reached final testing; use its final results rather than the development success alone. Its candidates still exclude reverse by the game's rule, but include every allowed turn even if it collides.
- **Two-call self-review:** the review changed two of 80 proposals, yielding zero wrong-to-shortest improvements and zero shortest-to-wrong regressions. Both initial and final review-workflow choices were shortest in 61/80 cases. It spent 160 requests for those 80 decisions and showed no measured correctness gain from its second call. The separate one-call priority batch scored 60/80; that one-state difference already existed in the review workflow's FIRST calls, so it is not evidence the second call helped.

## Recommended interface and exact prompts

The development-selected default is **{NAMES[preferred]}**. Review its held-out performance above before relying on it. Every payload is saved, and the frozen [policy builder](policy.py) generates exactly what was sent.

The priority instruction used by all non-original variants is:

> Choose the next Snake move. Your priorities are: (1) do not collide on this move; (2) reach the CURRENT food using as few moves as possible; (3) do not circle indefinitely. Food is eaten only when the head enters its cell. Each turn advances exactly one cell. Solid edges kill; touching body kills. The tail cell vacates unless this move eats food. No reverse turn. Infer safety and the route yourself from the observation. All three offered actions are possible commands, not necessarily safe commands.

The prose state describes the 12×12 board, coordinate convention, current heading, ordered head-to-tail cell list, current food coordinate, foods eaten and moves since food. It provides no recommendation. Choice descriptions map each command to its absolute heading and destination, as in the original baseline. That is an action-definition transform common to the comparison, not collision filtering.

For example, observations have the form “The snake faces north. Its cells in order from head to tail are: (6,6), (6,7), (6,8). Food is at (...).” The actual food coordinate is supplied from the board. The model must judge the route and safety itself.

## Tokens and latency per question

Every API request contains one `move` question. The provider's input/output usage includes observation and schema overhead. The CSV preserves each question exactly; the two review calls have separate `proposal` and `review` rows. Failed usage is unknown, not fabricated zero. Live QA calls are excluded. Failed request HTTP status counts: `{json.dumps(error_statuses,sort_keys=True)}`. No retry was attempted, and the precise provider-side cause is not established by these records.

The entire new study recorded **{successes:,} valid model requests** and **{failures} failed requests**, with **{inp:,} reported input** and **{out:,} output tokens** on recorded responses. These are accounting totals; individual costs are in the CSVs.

| Held-out policy | Valid questions | Mean input / question | Mean output / question | Median client request latency |
|---|---:|---:|---:|---:|
'''+ '\n'.join(cost_table)+f'''

[Screen per-question usage](records/screen-v1/per_question.csv) · [Development-game usage](records/development-v1/per_question.csv) · [Held-out usage](records/holdout-v1/per_question.csv)

Latency includes HTTP/network time. The game waits for replies; no fixed real-time deadline or missed-physics-tick experiment is performed. Playback speed is separate from model performance.

## Verification and limitations

The runner and policy never call the oracle. The offline analyzer reconstructs every request—including history and self-review—checks payload hashes, raw/parsed responses and model version, replays every state transition, verifies the executed action equals the model's final choice, and only then assigns shortest-action/legality labels. Raw runtime records and offline labels are separate files.

Policy tests forbid calls to safety, legal-move enumeration, distance or baseline functions during payload construction, verify all three commands stay available at a corner, check invertibility of head-relative geometry, verify that review sees only its own proposal, and ensure a failed review cannot silently fall back to its first answer. Existing engine/oracle tests remain applicable. Browser QA verifies replays and a real live move; live data stays outside frozen counts.

No model weights were changed. “Unassisted” here means no external evaluation or repair of action quality; observation formatting and explicit rule descriptions are still harness design. The rejected geometric variant additionally performs a declared coordinate transform. Results concern one pinned model version, a small synthetic board, an eight-food cap, selected prompt variants, and limited seeds. There is no proof of universal perfect accuracy, full-board completion, vision ability or global multi-food efficiency. No final-test failures were removed to improve the result.
'''
 (ROOT/'REPORT.md').write_text(text)
 replay={'metrics':metrics,'runs':read(R/'holdout-v1/verified_replays.json'),'preferred':preferred}
 (ROOT.parent/'web/unassisted-data.js').write_text('window.UNASSISTED_DATA = '+json.dumps(replay,separators=(',',':'))+';\n')
 dump={'valid_calls':successes,'failed_calls':failures,'input_tokens':inp,'output_tokens':out,'heldout_episodes':48,'development_episodes':16,'screen_decisions':640,'default_selected_on_development':preferred,'best_observed_on_holdout':best}
 (ROOT/'SUMMARY.json').write_text(json.dumps(dump,indent=2)+'\n');print(json.dumps(dump))
if __name__=='__main__':main()
