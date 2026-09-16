# Decision workflows, choice order and reasoning limits

This protocol and runnable cases are frozen before collecting this panel's
responses. The preceding reports informed the design; this is a new adaptive
study, not an independent benchmark replication.

## Planned scope

1,611 first-phase calls, then 288 dependent final-decision calls: 1,899 total.
Model `jev-1.13.0`; four workers; no retries; three repetitions per static
condition; shuffled order within each phase. Each request has one question.
A pipeline final request deliberately includes one previous model choice. No
other response history is sent. API/server-side independence is not guaranteed.

## Decision methods

Twelve new objects/services each have four scenarios: perform a service, perform
an in-person inspection, collect an item already at the shop, and book a future
appointment where the shop says not to bring the item. There are 48 scenarios,
balanced between bringing an item from home (24) and going without it (24).
The shop is nearby; the original car and walking/driving choice are not reused.
These objects are new to the published suites, but the task templates are related.

Each scenario has direct choices, descriptive choices and a prerequisite check,
with both option orders and three repetitions: 864 calls. A fourth condition
uses each actual prerequisite response to construct one final direct-choice
request: 288 calls. The final decision sees original facts plus the selected
check answer, including any incorrect or uncertain checks. No corrected answer,
expected label, probability, or confidence is supplied. Ground truth never enters
the final input. The generator `pipeline_cases` is fixed before the first run.
It preserves source run/trial/case/repetition for auditing.

Report final-decision accuracy separately from check accuracy and joint success.
Compare all three decision methods on the same scenario/order cells. Report both
final-stage tokens per question and the sum of check+decision costs per workflow;
the workflow sum is explicitly not a single-question token measurement. The
pipeline runs after phase one, so phase/time effects are not randomized away.
The direct instruction already asks about accomplishing the visit's purpose;
this is stronger wording than an unqualified everyday travel question.

## Choice permutations

Six new multiplication/subtraction/addition problems, four fixed choice IDs and
numeric meanings, every one of 24 permutations, three repetitions: 432 calls.
Every correct-answer position receives six permutations per problem. All numeric
options are distinct nonnegative integers. Report per-template performance,
accuracy by correct-answer position, and selection changes across permutations.
Do not infer a universal positional rule from six problems. No distractor-number
or instruction-prefix intervention is crossed into this panel.

## Difficulty curves

- Logic: chain depth 1/2/4/8/16/32 × three rule orders × true/false/unknown queries
  × three repetitions = 162 calls. Enumerating possible truth suffixes provides
  an independent finite-world oracle. This tests forward chaining, backward
  negation and invalid converse inference, not arbitrary propositional formulas.
- Tracking: 1/2/4/8/16 objects × three deterministic movement schedules × three
  repetitions = 45 calls. Five moves per object plus irrelevant visits. Increasing
  objects increases total events and text length, so these effects are confounded.
- Competing facts: 0/16/128/512 other-asset records × start/middle/end placement
  × three color rotations × three repetitions = 108 calls. Four target records
  disagree; the explicitly stated highest-version rule uniquely determines the
  answer. Target versions occur in order 2,4,1,3, so the last target mention is
  not the answer. With zero distractors the three placement labels duplicate the
  same text; they are baseline repetitions, not distinct contexts. Three color
  rotations are not exhaustive four-way answer-position balancing.

Hypotheses: descriptive choices or a live check improve decisions; fixed-ID
numeric choices vary with order; accuracy drops with one or more difficulty
axes. A ceiling result supports ability only through the tested range and does
not locate a failure boundary. No extrapolation to unlimited length or reasoning.

## Verification and publication

Run `python -m unittest -v test_limits_study` before paid requests. Freeze cases,
labels and schedule in each manifest before its calls. Validate payload hashes,
raw/parsed responses, model version, schedule completeness, selected choices,
probability fields and token usage. Reconstruct every pipeline input from its
actual saved source response. Preserve all outputs, including mistakes.

Publish full prompts, raw responses, per-question input/output CSVs, analysis,
source code, and an honest report to the existing isolated repository. Do not
publish credentials. Repetitions are stability measurements; no claim of 1,899
independent reasoning problems or population-level confidence intervals.

## Adaptive follow-up after the first phase

The first phase produced ceiling results in all three difficulty panels. Before
running the next calls we add 126 requests with separately frozen inputs:

- 54 scrambled-chain calls: depth 8/32/128 × two seeded code-name assignments ×
  yes/no/unknown × three repetitions. Rules are shuffled, category codes are
  opaque and there is a disjoint distractor chain. Unknown cases have a missing
  link. This changes structure as well as length, so compare within this panel.
- 18 carry/drop tracking calls: 8/16/32 people and items × two seeded event
  histories × three repetitions. People carry held items but leave dropped
  items behind. The queried item is finally dropped in one history and carried
  in the other. Each person handles one item; there are no handoffs.
- 54 dispersed-record calls: 128/512/1024 other records × winning record at
  start/middle/end × two color rotations × three repetitions. Lower target
  versions are dispersed at quarter positions. The highest version is uniquely
  correct regardless of its location. Two color rotations are not fully balanced.

Total planned calls including this adaptive extension: 2,025. This is a bounded
search for failures, not a promise to determine the largest possible input size.
