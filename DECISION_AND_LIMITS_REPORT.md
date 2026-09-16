# Jev: decision workflows, answer order and reasoning limits

This study adds **2,025 live requests** collected September 16, 2026, all returning
`jev-1.13.0`, with **zero API errors**. It follows the
[original behavior study](JEV_BEHAVIOR_REPORT.md) and
[everyday reasoning extension](EVERYDAY_REASONING_REPORT.md).

The results support three distinct conclusions:

1. **The tested decision methods tied.** Direct, descriptive and live two-step
   decisions each passed 288/288 on the same 48 scenarios. There is no measured
   advantage for the more expensive methods on this panel.
2. **Arithmetic answer order matters.** Across every permutation of four choices,
   accuracy was 95/108 with the correct choice first versus 62/108 when last.
3. **Task structure exposes failures that simple length tests miss.** Regular
   chains, explicit object moves and grouped versioned records stayed perfect.
   Scrambled/broken chains, implicit carrying, and dispersed middle-position
   records produced reproducible errors.

These are observed behavioral patterns in controlled synthetic tasks. They are
not proved internal rules, general-population accuracy estimates, or universal
context and reasoning thresholds.

## Design and prior commitments

The [protocol](LIMITS_PROTOCOL.md), [main suite](limits_study.py) and initial
label tests were committed as `8910c23` before requests began. The main phase
contained 537 conditions × three repetitions = 1,611 calls. It included direct
and descriptive decisions, prerequisite checks, arithmetic permutations, and
three difficulty axes. The actual saved check answers generated 288 final
requests, each with its own source-trial link.

All three original difficulty axes reached ceiling. We disclosed that result
and froze a bounded adaptive follow-up of 42 conditions × three repetitions =
126 calls in `9259e22` before collecting it. Its [generator](stress_followup.py)
changes task structure and raises some size limits. This is adaptive exploration,
not an untouched external validation set.

Four workers execute shuffled schedules within each phase. Every request has
one question, with no automatic retries. The two-stage method intentionally
forwards exactly one relevant earlier selected answer; other conversation and
trial history are absent. Fresh HTTP openers do not guarantee independent
server-side randomness or absence of caching. The pipeline's final calls occur
later than its checks and the direct comparisons, leaving a phase/time confound.

Ground truth uses exact arithmetic, graph reachability, finite chain worlds,
state simulation, explicit version rules and scenario constraints. Six offline
tests independently check the task generators and pipeline data flow. The
analyzer reconstructs every final payload from its saved source check, verifies
hashes and schedules, and grades selected choices rather than probability maxima.

## 1. Comparing complete decision methods

### Scenarios and interventions

Twelve objects/services cover laptop screen repair, violin strings, camera
sensor cleaning, printer rollers, sewing-machine motors, guitar adjustment,
vacuum inspection, blender blades, headphone cables, drone propellers, projector
lenses and console ports. Each object has four visit purposes:

- Perform the service on the item, which is at home: bring it.
- Have this exact item inspected in person at the shop: bring it.
- Collect the item, which is already at the shop: go without bringing it from home.
- Book a future appointment, with an explicit instruction not to bring the item:
  go without it.

The shop is a five-minute walk away. There are 24 bring and 24 go-without cases.
Both answer orders and three repetitions yield 288 trials per method. The objects
are new to the published suites, while the prerequisite task pattern is related
to earlier tests. Collection and booking deliberately make bringing the item
inappropriate or impossible.

Direct choices are “Bring it” and “Go without it.” Descriptive choices spell out
bringing the named item from home on this visit. Both use a purpose-focused
question; the direct baseline is already more explicit than the original bare
car-wash “walk or drive?” question.

The pipeline first asks whether the purpose requires bringing the item from
home, allowing yes/no/cannot_be_determined. Its final call receives the original
facts and the **actual selected check answer**, followed by the original direct
question. It receives no expected label, correction, confidence or probabilities.

### Results and per-question usage

| Stage or method | Correct / requests | Accuracy | Mean input tokens/question | Mean output tokens/question |
|---|---:|---:|---:|---:|
| check | 288/288 | 100.0% | 402.81 | 42.00 |
| described | 288/288 | 100.0% | 387.31 | 32.50 |
| direct | 288/288 | 100.0% | 365.81 | 32.50 |
| pipeline | 288/288 | 100.0% | 405.81 | 32.50 |

`check` is a prerequisite classification, not a final action. Direct, described
and pipeline rows are comparable final decisions. Every method passed all 72
trials in each visit-purpose category and all 144 trials under each answer order.
All 288 check/final pairs were jointly correct.

The whole two-question workflow averaged **808.63 input and 74.50 output tokens
per completed decision**, compared with 365.81 input and 32.50 output for one
purpose-focused direct question. These workflow figures are sums across two
questions, not per-question usage. The individual stage costs are in the table.

### What this establishes—and does not

We successfully tested a real two-stage pipeline, rather than supplying manually
verified prerequisite facts. But direct accuracy was already 100%, so there is
no evidence here that either intervention improves accuracy. Additional calls
and longer descriptions cost tokens without a measured gain on these scenarios.

There were **zero wrong or uncertain prerequisite answers**, so this live panel
cannot measure whether the final call repairs or amplifies a bad check. An offline
construction test confirms that an uncertain answer would be forwarded unchanged;
that is a software property, not observed model recovery behavior.

Do not read this as a reversal of the earlier car-wash failures. The domain,
choices, explicit purpose, and scenario constraints all changed. This panel
supports the narrower conclusion that Jev handles these purpose-focused item
transport decisions. It cannot isolate which wording or domain feature made
them easier, or establish a universally best decision workflow.

## 2. All answer permutations on arithmetic

Six new problems require boxes × pens per box − sold + received. Four distinct,
nonnegative candidate values have fixed IDs and meanings. Each of the 24 orders
runs three times, giving 72 requests per problem and **432 total**. Every correct
position has six permutations per problem, so correct position is fully balanced
within each problem.

| Correct choice position | Correct / requests | Accuracy | Mean input tokens/question | Mean output tokens/question |
|---|---:|---:|---:|---:|
| 1 | 95/108 | 88.0% | 381.33 | 50.00 |
| 2 | 67/108 | 62.0% | 381.33 | 50.00 |
| 3 | 64/108 | 59.3% | 381.33 | 50.00 |
| 4 | 62/108 | 57.4% | 381.33 | 50.00 |

The combined result was **288/432 (66.7%)**. Correct-first accuracy exceeded
correct-last by **30.6 percentage points**. Mean token usage was identical across
positions, so the measured contrast is not explained by a change in reported
input length. Other choices also move in each permutation; their relative
ordering may interact with the correct choice's position.

| Problem | Correct value | Correct / 72 | Permutations correct in all three repeats |
|---|---:|---:|---:|
| 4 × 9 − 7 + 3 | 32 | 72 | 24/24 |
| 8 × 7 − 11 + 5 | 50 | 72 | 24/24 |
| 13 × 11 − 23 + 8 | 128 | 32 | 8/24 |
| 27 × 16 − 73 + 21 | 380 | 23 | 5/24 |
| 43 × 19 − 97 + 32 | 752 | 60 | 19/24 |
| 132 × 25 − 329 + 61 | 3032 | 29 | 5/24 |

The first two problems were invariant and correct; the other four selected
multiple numeric answers across the recorded permutations and repetitions.
For example, the third problem selected 128 on 32 calls and 120 on 40. The latter
matches omitting the received eight pens. Across the panel, **131 of 144 errors**
selected the candidate that omits the received quantity; the remaining 13 selected
the candidate that subtracts it. This describes output patterns, not proof of
which computation occurred internally.

The study confirms order sensitivity on this set more thoroughly than the earlier
two-order comparison. It does not establish that Jev always picks the first
choice, that first is optimal on every problem, or that a majority vote over
permutations reliably fixes errors. Correct answer ID `v0` remained fixed; IDs
were not independently counterbalanced. Six arithmetic templates remain a small,
correlated sample, and no population significance claim is made.

## 3. Increasing difficulty: regular versus harder structure

### Regular logical chains

The first panel uses one-way category chains at depths 1, 2, 4, 8, 16 and 32,
three rule orders, and necessarily true/necessarily false/unknown queries. All
**162/162** answers were correct, including backward propagation of a negative
fact through the implication chain. Explicit answer definitions avoid the
entailment/truth-status ambiguity disclosed in the earlier report.

| Links in regular chain | Correct / requests | Accuracy | Mean input tokens/question | Mean output tokens/question |
|---|---:|---:|---:|---:|
| 1 | 27/27 | 100.0% | 390.33 | 43.33 |
| 2 | 27/27 | 100.0% | 407.33 | 43.33 |
| 4 | 27/27 | 100.0% | 441.33 | 43.33 |
| 8 | 27/27 | 100.0% | 509.33 | 43.33 |
| 16 | 27/27 | 100.0% | 659.33 | 43.33 |
| 32 | 27/27 | 100.0% | 963.33 | 43.33 |

The regular category names and simple chain topology may make this family easy.
The follow-up therefore uses opaque code names, shuffled rules, a disjoint
irrelevant chain, and missing links in unknown cases. It has two seeded instances
per depth/truth-status cell, each repeated three times.

| Links in underlying scrambled chain | Correct / requests | Accuracy | Mean input tokens/question | Mean output tokens/question |
|---|---:|---:|---:|---:|
| 8 | 12/18 | 66.7% | 675.67 | 42.00 |
| 32 | 7/18 | 38.9% | 1539.67 | 43.11 |
| 128 | 6/18 | 33.3% | 4995.67 | 43.33 |

| Depth | Necessarily true | Necessarily false | Unknown because a link is missing |
|---|---:|---:|---:|
| 8 | 6/6 | 6/6 | 0/6 |
| 32 | 6/6 | 1/6 | 0/6 |
| 128 | 6/6 | 0/6 | 0/6 |

All **18/18 forward-true** answers passed. None of the **18 missing-link** cases
were correctly classified as unknown. Negative backward inference degraded
from 6/6 to 1/6 to 0/6. Overall scrambled-chain accuracy was **25/54**.

This is a concrete weakness that the regular chains concealed. It does not mean
all logic beyond eight links fails: forward-true cases still passed at 128.
Opaque names, distractors, link completeness, ordering and depth are not all
independently crossed here; the regular-to-scrambled contrast cannot assign
causation to one feature. Even within the scrambled family, different depths
use different seeded instances.

### Object count versus carrying state

Explicit move histories stayed correct in **45/45** calls across 1, 2, 4, 8 and
16 objects, with five moves per object plus visits that do not move anything.
Increasing objects also increases event count and text length, so those dimensions
are confounded.

The harder panel requires inferring an item's movement from whether its person
is holding it. A dropped item stays put while its person moves; a held item goes
with the person. People handle only their own item, with no handoffs.

| People and objects | Correct / requests | Accuracy | Mean input tokens/question | Mean output tokens/question |
|---|---:|---:|---:|---:|
| 8 | 3/6 | 50.0% | 1141.00 | 48.00 |
| 16 | 6/6 | 100.0% | 2027.00 | 47.50 |
| 32 | 3/6 | 50.0% | 3867.00 | 48.00 |

This follow-up scored **12/18**. Errors appeared with eight and 32 objects, while
16 passed. The two failed configurations were the histories whose queried item
was still being carried; the dropped-item configurations passed. With only two
histories at each size, this is not a monotonic capacity boundary. It suggests
that representing carrying state is worth testing separately from explicit
object-location updates.

### Competing records and middle placement

Initially, all **108/108** versioned-record questions passed with 0, 16, 128 or
512 other records. The four conflicting TARGET records were grouped together,
and the prompt explicitly selected the highest version. The highest target
version was not the last target mention. At zero distractors, placement labels
are duplicate contexts, not three different positions.

The harder panel disperses lower TARGET versions at quarter positions and moves
version 4—the winner—to the beginning, middle or end. The rule stays highest
version, regardless of text order. Each cell has two color rotations repeated
three times.

| Other records / winning-record position | Correct / requests | Accuracy | Mean input tokens/question | Mean output tokens/question |
|---|---:|---:|---:|---:|
| 128 / end | 6/6 | 100.0% | 2182.00 | 45.00 |
| 128 / middle | 6/6 | 100.0% | 2182.00 | 45.00 |
| 128 / start | 6/6 | 100.0% | 2182.00 | 45.00 |
| 512 / end | 6/6 | 100.0% | 7558.00 | 45.00 |
| 512 / middle | 1/6 | 16.7% | 7558.00 | 45.00 |
| 512 / start | 6/6 | 100.0% | 7558.00 | 45.00 |
| 1024 / end | 6/6 | 100.0% | 14726.00 | 45.00 |
| 1024 / middle | 0/6 | 0.0% | 14726.00 | 45.00 |
| 1024 / start | 6/6 | 100.0% | 14726.00 | 45.00 |

The result was **43/54**. Beginning and end passed every cell. Middle placement
passed 6/6 with 128 other records, dropped to 1/6 with 512, and reached 0/6 with
1,024. The latter size used **14,726 reported input tokens per question**, equally
across all three positions.

All eleven wrong selections matched TARGET version 3 rather than version 4.
That is consistent with losing or underweighting the higher-version middle
record, but does not prove an attention mechanism or a universal recency rule:
the beginning-position winner remained correct despite later lower versions.

Unlike the earlier plain lookup test, this harder task provides evidence of
position sensitivity at the tested larger sizes. It remains a synthetic
highest-version selection task, with just two color rotations and no external
replication. It does not establish that ordinary documents fail at 7,558 or
14,726 tokens, nor locate the API's maximum context window.

## Interaction guidance supported by the combined studies

1. **Use precise task and answer semantics.** Purpose-focused direct decisions
   worked on this new panel. Explicit truth-status options are preferable to
   ambiguously mixing “not entailed” with “false.” These are tested prompt
   packages, not proof that every component is necessary.
2. **Do not add a pipeline automatically.** Here it doubled calls and increased
   total input tokens roughly 2.21× with no gain. Use a multi-step method when
   task-specific evaluation demonstrates a benefit; this panel cannot validate
   its behavior when the first step is wrong.
3. **Compute exact arithmetic outside the model.** Permutation testing exposed
   fragility; neither first-position placement nor repeated agreement guarantees
   correctness. Earlier letter-counting failures support the same advice for
   exact symbolic operations.
4. **Test missing links and negative cases, not just successful chains.** A model
   passing long positive examples can still miss that a required implication is
   absent or fail backward inference.
5. **Treat long conflicting context as a separate task.** Prefer deterministic
   selection of the latest/highest-version record when that rule is available,
   then supply the selected evidence. That engineering recommendation follows
   from having an exact external rule; a preprocessing workflow was not evaluated
   in these calls. Do not assume that moving facts alone solves every task.

The best method remains task-dependent. This study found specific strengths,
failed invariances, and cases where extra prompting brought cost without gain.
It did not discover a single instruction that makes Jev uniformly reliable.

## Evidence, per-question tokens and reproduction

All new requests have one question. Each `per_question.csv` contains exact
reported input/output usage, selected answer, expected answer and grade for every
trial. These counts include the complete API-counted context/schema and overhead;
they are not just tokens in the human-visible question sentence.

- Main phase: [results/20260916T124604860296Z-limits-study/manifest.json](results/20260916T124604860296Z-limits-study/manifest.json); [results/20260916T124604860296Z-limits-study/results.jsonl](results/20260916T124604860296Z-limits-study/results.jsonl);
  [results/20260916T124604860296Z-limits-study/per_question.csv](results/20260916T124604860296Z-limits-study/per_question.csv).
- Pipeline: [results/20260916T124845798330Z-decision-pipeline/manifest.json](results/20260916T124845798330Z-decision-pipeline/manifest.json); [results/20260916T124845798330Z-decision-pipeline/results.jsonl](results/20260916T124845798330Z-decision-pipeline/results.jsonl);
  [results/20260916T124845798330Z-decision-pipeline/per_question.csv](results/20260916T124845798330Z-decision-pipeline/per_question.csv); [results/20260916T124845798330Z-decision-pipeline/workflow_usage.csv](results/20260916T124845798330Z-decision-pipeline/workflow_usage.csv).
- Stress follow-up: [results/20260916T125040590877Z-stress-followup/manifest.json](results/20260916T125040590877Z-stress-followup/manifest.json); [results/20260916T125040590877Z-stress-followup/results.jsonl](results/20260916T125040590877Z-stress-followup/results.jsonl);
  [results/20260916T125040590877Z-stress-followup/per_question.csv](results/20260916T125040590877Z-stress-followup/per_question.csv).
- Machine-readable combined metrics: [results/20260916T124845798330Z-decision-pipeline/limits_summary.json](results/20260916T124845798330Z-decision-pipeline/limits_summary.json).

`workflow_usage.csv` keeps source and final trial IDs, separate stage costs, joint
correctness, and explicitly labeled summed workflow costs. Each final input is
reconstructed exactly from its source in the offline analyzer. No actual check
was corrected or discarded, and no failure was retried.

Offline reproduction:

```sh
python -m unittest -v test_limits_study test_everyday_study
python analyze_limits_study.py results/20260916T124604860296Z-limits-study results/20260916T124845798330Z-decision-pipeline results/20260916T125040590877Z-stress-followup
python verify_results.py
python build_limits_report.py
```

For new paid calls, use `python limits_study.py`, then
`python run_decision_pipeline.py results/<new-limits-study>`, then
`python stress_followup.py`. Provide `TYPESAFE_API_KEY` via the environment or an
ignored local `.env`. The first and third support `--plan-only`; the pipeline
also supports it when a complete source run is supplied. New outputs receive
new directories. Future responses are not guaranteed to reproduce these outcomes.

The repository now preserves **11,621 successful requests and 13,096 answers**,
plus two historical failed startup attempts. The 72 ambiguous pilot questions
from the previous extension remain excluded from that report's substantive
accuracy claims; they remain part of the evidence inventory. The new study has
no such scoring exclusions.

## Scope and unresolved limits

Three repetitions are not independent new problems. Most panels reuse narrow
synthetic templates; many conditions deliberately have explicit constraints.
The arithmetic and stress panels are too small to infer population-level rates.
The follow-up was selected after ceiling results and must not be presented as
an untouched held-out benchmark.

We verified the hosted API's returned model name, inputs and outputs, not its
weights, hidden prompts, cache or sampling implementation. Correlated outputs
and shared provider state remain possible. No internal reasoning trace was
available. Observed answer patterns alone do not establish mechanisms.

We located failures in harder logic, carrying and long competing-record tasks,
while other tasks stayed perfect through the tested range. We did not determine
an absolute depth, object-count or context boundary; carrying performance was
not even monotonic. The decision panel left the comparative-benefit hypothesis
unresolved because every method passed. Those are findings and limitations,
not missing results to conceal.
