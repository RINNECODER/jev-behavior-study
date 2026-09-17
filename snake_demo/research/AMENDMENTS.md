# Adaptive extensions and implementation notes

## 2026-09-17: longer-game transfer check (before its execution)

The eight-food experiment only evaluates a short task. In addition to the
predeclared 100-seed short-game code-only stress test, run the exact code-only
planner on 16 new seeds 4001–4016 with target 24, maximum 600 moves, and the same
50-move no-food limit. This is an exploratory test of the planning component's
scope, not another estimate of Jev accuracy. Do not include it in the frozen
16-seed model completion rates. Retain planner-budget errors and dead ends.
If this reveals failures, a perfect short benchmark must not be generalized to
full-length Snake. No future food will be read by the planner.

## Verification implementation correction

JSON serialization changes Python tuples into arrays. The first diagnostic
verification compared an in-memory tuple in the atomic-question destination
against its saved JSON list and stopped. The verifier was corrected to compare
JSON-normalized structures. No API request, evidence, prompt, label, scoring
rule, or partition was changed and no failed API call was hidden.

## Assistance attribution

The same-state exact variant contains solved route costs. Its successful model
selection tests minimum-number compliance, not route computation. Exact
verification runs may have zero actual overrides while still relying on code
assistance on every move. Baseline and model ties can choose different shortest
paths and consequently receive different future food positions.

## 2026-09-17: bounded route certificates, declared before v2 tests

Long-game seed 4001 stopped at food 15 because the original per-action exact
solver exhausted its node budget on left, despite finding a six-move right
route. This is a search-budget failure, not evidence of an unavoidable collision.

Implement a separate v2 planner: solve for the optimum D once, then exhaust only
paths of length <=D for each candidate first move. A candidate with no such path
gets a certified lower bound D+1, NOT a claim of unreachability. Root search and
bounded searches retain the 100,000-node limit and explicit unknown status.
Compare its optimal-action sets with v1 on the frozen 120-state corpus. Re-test
code-only on all 16 previously selected long-game seeds as DEVELOPMENT, retaining
v1 failures. Test code-only on fresh long-game seeds 5001–5016. These are tests
of code, not Jev. If any remain unresolved or fail, retain them as limits.

Only if the 16 fresh code-only long games pass will this extension run a fresh
16-seed Jev selection test with the new certified lower-bound facts, using seeds
6001–6016, 24-food target, 600 moves, 50 without food. No verifier replacement
will be used in those model games. Report this conditional design and assistance;
a supplied lower bound is a planner result, not Jev computing a route.

## 2026-09-17: exploratory equal-priority tie-break probe

After the fresh v2 long-game test left seed 5006 unresolved at food 23, treat
that failure state as development evidence. Probe the same exact A* heuristic
and 100,000-node budget with deeper states preferred on equal f priority
(`deep_tie.py`). It still exhausted the budget at 100,001 expanded states.
The full probe and source state are saved in
`records/deep-tie-development-probe.json`. This failed single-state diagnostic
was not promoted into a controller or portrayed as a fresh holdout test. It
uses no Jev calls. No second hidden test batch was selected to erase the failure.
