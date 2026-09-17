# Unassisted Classic Snake: frozen protocol

## Boundary of this study

Pinned model `jev-1.13.0`, Classic 12×12 Snake, eight-food target, 200 moves,
50 moves without food. All model actions execute unchanged. No legal-move mask,
safe-action flag, distance, shortest route, candidate quality score, planner
recommendation, fallback, corrected answer or oracle-selected example is sent.
The game engine enforces its rules after a decision. Offline scoring happens
ONLY after calls/games finish and cannot stop or alter a trajectory.

Head-relative coordinates are explicitly labeled geometric preprocessing: a
rotation/translation of every body point, food and board boundary, with no
quality judgment. This tests unassisted action selection with a transformed
observation, not literally unchanged raw coordinates. Absolute direction labels
and candidate destinations encode the game's action meanings, not action merit.
History contains only prior observations and executed model moves. Two-call
review adds only the first model's own proposal; no ground truth or solver output.
There is no model training, weight update, or image input.

## Hypotheses and frozen candidates

1. `original`: the existing full-state/direct prompt, control.
2. `priority`: compact coordinates with explicit ordered goals: survive this
   move, reach current food quickly, avoid endless circling; static rule reminder.
3. `narrative`: the same observations described in prose rather than JSON fields.
4. `ascii`: priority plus a whole-board character grid, retaining body order.
5. `egocentric`: priority with head at (0,0), positive y forward and x right,
   all geometry transformed consistently. No distances or action rankings.
6. `history`: priority plus four prior observations/actions from the trajectory.
7. `absolute`: priority with north/east/south/west choice keys for the three
   non-reversing actions. No collision filtering.
8. `review`: priority proposal followed by a second independent request using
   the same observation and that proposal; ask Jev to retain/revise its own move.
   This is an unassisted two-call workflow, with twice the call opportunities.

Hypotheses concern representation, instruction priority, memory, action encoding,
and model self-review. Multiple fields change in some variants, so an observed
improvement is an effect of the whole variant, not proof of one internal cause.

## Selection, sample sizes and stopping

- Screening: select 80 unique board states uniformly without replacement from
  all 16 previous unassisted held-out Classic games (seeds 1001–1016). These are
  NOW DEVELOPMENT data, not a reused holdout. Preserve up to four actual prior
  model moves/observations. Selection uses no solver labels or correctness filter.
  Eight variants × 80 states = 640 decisions / at most 720 requests. Shuffle
  jobs with a frozen seed; balanced candidate ordering across paired states.
- Select the top three non-original variants by shortest-action count divided
  by attempted decisions on this DEVELOPMENT screen; ties use legality count,
  then fewer requests, then the listed order above. Unknown oracle labels are
  reported and cannot earn a correct score. Keep original as a control.
- Development games: those three variants plus original × seeds 8101–8104,
  giving 16 games. Select the two best non-original variants by target successes,
  total food, shortest-action fraction (unknown scores count against ranking),
  then fewer requests and frozen variant order. Freeze this choice before new
  held-out games. Single-state accuracy alone is not final evidence of gameplay.
- Final held-out games: original plus the two selected variants × new seeds
  9101–9116 = 48 games. No prompt edits, parameter changes, retries, replacements,
  or selection of a better-looking batch after this stage. Existing original
  results are context only; the contemporaneous 16-seed control is primary.
- At most 26,320 paid API requests for the full design (720 screening + at most
  6,400 development + 19,200 held-out); actual game termination usually reduces
  this. Four workers, sequential turns within each game. Stop after this protocol
  and report actual results; never claim universal perfection from a sample.

## Evidence and statistics

Save manifest before each stage, model version, complete payload/response,
payload hash, call start/latency/status, per-question input/output tokens, each
proposal/final choice, and every game state before/after. All calls contain one
question. Review has separate proposal/review token rows; do not average away
its extra calls. Failures remain recorded and terminate the affected decision or
game with unknown failed-call usage. No automatic retries. API requests contain
no conversation history beyond each explicitly constructed observation/history.
Client-side isolation does not establish server-side independence/caching policy.

Offline scorer replays the engine and reconstructs every payload. It evaluates
legality and exact shortest first actions with dynamic tail movement, using the
existing bounded-certificate oracle only after decisions. Unknown search results
stay unknown; report their count. Score completed food segments separately from
whole-game success; surviving without reaching food is not a success.

Primary comparison: held-out target completion and food score. Secondary:
shortest-action/legality, stalls/collisions, repeats, token and latency cost,
self-review revisions. Show denominators, paired seed wins/losses, and Wilson
intervals on game completion. Move-level samples are correlated. No causal
mechanism claim or uncorrected multiple-testing significance claim. Subsequent
food can diverge between policies due to occupied-cell sampling.
