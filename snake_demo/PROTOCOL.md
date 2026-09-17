# Snake experiment protocol

A procedural 12×12 Snake game with structured JSON state, not image input.
Jev chooses relative left/straight/right. The initial snake has three cells.
State, candidate destinations and action descriptions are identical between
Jev profiles except that the guarded profile removes immediately fatal choices.
Choice order rotates by seed plus move number. No pathfinding hints or reasoning
from another model are supplied to Jev.

## Profiles and assistance

- **Jev direct:** the model chooses from all three non-reversing moves.
- **Jev guarded:** code filters immediately fatal moves. When only one safe move
  remains, code executes it without calling Jev. With no safe move, a deterministic
  move ends the game. Forced moves are counted and labeled separately. This is
  an assisted system, not a claim of unaided model skill.
- **Baseline:** deterministic breadth-first distance-to-food selection among
  legal relative moves, with a fixed tie break. It has no API calls, is not an
  optimal solver, and can trap itself or loop.

One decision advances one cell. Network waiting never advances the board.
This isolates decision quality from latency; it is not fixed-rate real-time
control and no calls-per-second guarantee is claimed.

## Difficulty

All levels use a 12×12 board. Open wraps at edges and has no obstacles. Classic
has solid boundaries and no obstacles. Obstacles has solid boundaries and 12
seeded blocked cells; Dense has 24. Obstacle placement preserves connectivity
of free terrain and reserves the initial snake and first forward cell.
These are intended difficulty variants; monotonically worse scores are not assumed.

Food is uniformly sampled from unoccupied, unblocked cells. Moving into the tail
cell is legal when it vacates on that turn. Eating increases length by one.
A game ends on collision, 8 collected foods, 200 moves, or 50 consecutive moves
without food. Reaching eight foods is a capped task success, not filling the board
or establishing maximum possible Snake skill.

## Runs

First, a three-episode API/rules pilot uses seed 11, Classic, all three profiles,
a 30-move cap and three-food target. Pilot results are preserved separately and
excluded from main estimates. The prompt is fixed before the pilot; changes
made after pilot inspection must be disclosed.

Main benchmark: seeds 101–108 × four levels × three profiles = 96 episodes.
There are 64 Jev-profile games and 32 deterministic baseline games, at most
12,800 Jev requests (actual requests are fewer due to termination and forced
moves). Four episodes run concurrently; episode order is shuffled with seed
20260923. No automatic retries. Failed API episodes remain visible.

The same initial seed is paired across controllers, but later food positions
can diverge because occupied cells affect sampling. Seeds are eight scenario
instances per level/profile, not independent observations for each move.

## Evidence and metrics

Freeze this protocol, engine and prompt before the main run. Save each requested
payload, raw response, input/output tokens, selected action, before/after state,
and latency. Verify every transition by replaying the deterministic engine,
regenerating payloads and confirming action and usage totals. Report mean/median
food, best score, eight-food success count, endings, forced moves, per-call latency
and token usage. Publish all games, not only successful clips. The UI labels any
best-game selection as a selected replay, not typical performance.

The replay speed is user-controlled and separate from recorded inference latency.
Local live mode uses the same engine and controllers; credentials remain on the
server. Static hosting supports saved replays and does not make API requests.
The design intentionally uses code-rendered grid cells rather than illustrated
sprites so that visible cells exactly match the collision and observation model.
