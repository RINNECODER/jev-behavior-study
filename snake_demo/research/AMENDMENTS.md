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
