# Jev 1.13.0: everyday reasoning and exactness extension

Published evidence collected September 16, 2026. This extension adds **1,791 live
requests**, across **199 base configurations and 597 prompt conditions**, to the
[original behavior study](JEV_BEHAVIOR_REPORT.md). All responses returned
`jev-1.13.0`; there were zero API errors in these two new runs.

**Main finding:** Jev performed consistently on these explicit, constrained
logic, retrieval, tracking and prerequisite tasks. Exact letter counting and
multi-step arithmetic were much less reliable. Generic evidence-only prompting
was not a universal fix. These observations describe the hosted choice API on
this synthetic suite, not the model's internal algorithm or general intelligence.

## Research basis and what is new

The original study concentrated on the car-wash decision, prerequisite checks,
letter counting and repeated filler. This extension asks whether that behavior
transfers to other everyday reasoning skills and more diverse inputs.

[bAbI](https://arxiv.org/abs/1502.05698) motivates separating elementary skills,
including deduction and tracking facts. [GSM-Symbolic](https://arxiv.org/abs/2410.05229)
motivates paired numerical variants and irrelevant-detail controls.
[Lost in the Middle](https://arxiv.org/abs/2307.03172) motivates changing the
position of a requested record within a larger context. We created original
questions inspired by these methods; we did not run or reproduce those official
benchmarks, and our scores cannot be compared directly with their scores.

The exact design, research links, hypotheses, interpretation rules and commands
are in [EXTENSION_PROTOCOL.md](EXTENSION_PROTOCOL.md). The runnable suites are
[everyday_study.py](everyday_study.py) and
[reasoning_followup.py](reasoning_followup.py).

## Design, grading and an important correction

The pilot used 93 base configurations × three prompt modes × three repetitions
= 837 requests. The adaptive follow-up used 106 × three × three = 954.
A base configuration can be a paired transformation of the same underlying
problem: for example a spaced string or a version with irrelevant numbers.
Thus 199 is not a count of 199 independent reasoning templates.

The modes are:

1. Plain: the task's ordinary instructions and original choice order.
2. Reversed: identical facts and instructions, with choice order reversed.
3. Explicit: original order plus “Use only the supplied facts and rules. Do not
   assume unstated facts. Check the exact requested condition before selecting
   an answer.”

Each request has one question, no conversation history, no previous answers,
and a fresh HTTP opener. Four workers execute a shuffled, interleaved schedule;
there are no retries. Exact payloads, expected answers and schedules were saved
before their respective runs. We cannot verify independence of provider-side
randomness or caching. Repeated calls measure observed stability, not independent
problem coverage.

**Pilot label correction:** the original conditional question asked “Does it
follow that …?” Our automatic key used `cannot_be_determined` for an unknown
proposition. But answering `no` can correctly mean that the proposition does not
follow. Accordingly, **all 72 pilot conditional requests are excluded from
substantive accuracy claims**, rather than selectively removing apparent
failures. The saved manifest, raw outputs, and original automatic `analysis.json`
scores are retained. `extension_metrics.json` and `per_question.csv` mark this
family `score_eligible: false`; extension ALL aggregates exclude it.

The follow-up explicitly defines the three answers as necessarily true,
necessarily false, or either truth value possible. It also says no converse rule
is stated. This repairs the interpretation but changes multiple prompt details;
it is not proof that one added sentence caused an improvement. The follow-up
was designed after examining the pilot and is labeled adaptive throughout.

Labels come from finite truth tables, exact arithmetic/character counts, simple
state tracking, and explicit scenario constraints. We reviewed the task meanings
and ran independent prompt-parsing checks for arithmetic, retrieval and tracking.
The offline analyzer verifies request hashes, schedules, raw/parsed responses,
model version, options, selected-answer grades and reported token usage.

## Pilot results: strong performance on constrained tasks

The 765 eligible pilot requests were all correct. This supports narrow capability
claims, with an important ceiling limitation: the tasks were too easy to show
whether the prefix or reversed order helps on these skills.

| Skill | Plain | Reversed choices | Evidence-only prefix |
|---|---:|---:|---:|
| arithmetic | 36/36 (100.0%) | 36/36 (100.0%) | 36/36 (100.0%) |
| decimal | 18/18 (100.0%) | 18/18 (100.0%) | 18/18 (100.0%) |
| evidence | 18/18 (100.0%) | 18/18 (100.0%) | 18/18 (100.0%) |
| negation | 12/12 (100.0%) | 12/12 (100.0%) | 12/12 (100.0%) |
| object tracking | 24/24 (100.0%) | 24/24 (100.0%) | 24/24 (100.0%) |
| ordering | 18/18 (100.0%) | 18/18 (100.0%) | 18/18 (100.0%) |
| prerequisite | 24/24 (100.0%) | 24/24 (100.0%) | 24/24 (100.0%) |
| quantifiers | 24/24 (100.0%) | 24/24 (100.0%) | 24/24 (100.0%) |
| retrieval | 81/81 (100.0%) | 81/81 (100.0%) | 81/81 (100.0%) |

- **Negation:** four truth/negation combinations; no test of deeply nested negation.
- **Quantifiers:** eight cases covering all/some/none, category membership,
  non-converse inference and existence. The prompt explicitly allowed empty
  categories under classical logic.
- **Arithmetic:** six small addition/subtraction examples, each with/without an
  irrelevant spotted-apple detail. Keeping spotted apples did not change totals.
- **Decimals:** six comparisons, including 9.11 versus 9.9 and 10.0 versus 10.00.
- **Tracking and ordering:** eight short key-location stories and six arrival-order
  configurations. The target was the object location, not simply the last room
  mentioned.
- **Prerequisites:** four objects/services (coat, watch, bicycle, document), each
  with the object at home or already at the shop. The physical-presence rule was
  supplied explicitly. This tests applying a stated condition, not independently
  discovering an unstated real-world requirement.
- **Evidence use:** six cases, including missing color/time information and
  fictional facts that override ordinary-world expectations.

These results strengthen the distinction from the original car-wash result:
Jev can answer many explicit conditions correctly. They do not establish that
it will spontaneously use those conditions when selecting an everyday action.
The prerequisite tasks here also use simpler yes/no questions than a full plan.

## Retrieval and text length

The lookup panel contains 16, 128 or 512 generated records, with target records
at the beginning, middle or end. Three code-offset samples and three modes
produce 27 requests per size/position cell. **Every cell scored 27/27**, for
243/243 overall. The largest request reported **7,041 input tokens**.

The records are distinctive fixed-format key/value sentences, with four choices.
They are not natural documents containing ambiguous references or competing
arguments. There was no observed middle-position penalty on this task. That
neither disproves such effects on harder tasks nor establishes the API's maximum
context length. The earlier study used longer repeated filler, up to 11,496
reported input tokens, but that is a different task and text distribution.

## Follow-up: clearer logic passes; exactness separates the tasks

| Skill | Plain | Reversed choices | Evidence-only prefix |
|---|---:|---:|---:|
| conditional truth | 192/192 (100.0%) | 192/192 (100.0%) | 192/192 (100.0%) |
| exact count | 39/72 (54.2%) | 39/72 (54.2%) | 39/72 (54.2%) |
| long tracking | 18/18 (100.0%) | 18/18 (100.0%) | 18/18 (100.0%) |
| multistep math | 29/36 (80.6%) | 18/36 (50.0%) | 25/36 (69.4%) |

### Conditional truth status

Eight rule templates each have eight observation/query combinations, including
modus ponens, modus tollens, direct known facts and cases where a converse or
inverse inference would be invalid. All **576/576** choices matched the truth-table
labels across the three modes.

For example: if a switch is on, its lamp is lit; the lamp is lit; is the switch
on? Under the explicitly defined answer semantics, both switch states are
possible, so `cannot_be_determined` is correct. Jev selected it correctly in the
follow-up. We do not use the pilot's ambiguous “Does it follow?” answers as
counterevidence.

This is strong observed performance on short, one-rule problems. It does not
cover arbitrary logical depth, contradictions, natural-language ambiguity,
or combining many rules into a proof.

### Exact character counting

The twelve strings include ordinary words, synthetic repeated letters,
mixed case and underscore separators. Each appears as contiguous and spaced
text. The task explicitly says to ignore case and count occurrences of `r`.
Across all modes the result was **117/216 (54.2%)**.

| Text format | Plain | Reversed | Explicit |
|---|---:|---:|---:|
| Contiguous | 18/36 | 18/36 | 17/36 |
| Spaced | 21/36 | 21/36 | 22/36 |

Spacing improved aggregate counts modestly in this set, but did not make counting
reliable. It could also harm individual items. For example, `rarer` has three
r's: the contiguous plain version passed 3/3, while the spaced plain version
selected four 3/3. `raven` has one r, yet every one of its 18 requests selected
two, across both text formats and all modes. `mirror` has three; 17/18 requests
selected two, with one correct explicit/spaced response. These are task failures
against straightforward character-count oracles, not interpretive disputes.

The plain contiguous `raven` condition had mean reported confidence 0.83 while
being wrong 3/3. Therefore confidence is not a correctness guarantee. We do not
interpret that score as an empirically calibrated probability of success.

The explicit prefix scored exactly the same aggregate 39/72 as both other modes,
while individual outcomes changed. Equal aggregate accuracy is not evidence that
the prompts are behaviorally identical.

### Multi-step arithmetic and irrelevant information

Six numerical templates require multiplication, subtraction and addition. Each
has a matched version with irrelevant shelf/chair counts. Results total
**72/108 (66.7%)**, much lower than the pilot's simpler arithmetic.

| Irrelevant numbers | Plain | Reversed | Explicit |
|---|---:|---:|---:|
| Absent | 15/18 | 12/18 | 15/18 |
| Present | 14/18 | 6/18 | 10/18 |
| Combined | 29/36 | 18/36 | 25/36 |

Reversing options reduced accuracy by 11/36 requests, or 30.6 percentage points,
on this matched panel. The evidence-only prefix also failed to improve the
plain result. This is an observed contrast in six templates with three repeated
calls per configuration, not a universal effect size or a significance claim.

One concrete failure: 23 boxes × 14 pencils − 61 sold + 19 received = **280**.
All 18 requests across noise and mode variants selected **242**, which equals
23 × 14 − 61 − 19. This is consistent with subtracting the received quantity on
that item, but it does not expose the model's internal computation. Other errors
and mixed outcomes are preserved in the raw evidence.

Correct answers occupied the first option in the original arithmetic ordering
and the last after reversal. Consequently this experiment establishes sensitivity
to that order change, not a fully randomized estimate of general position bias.
We did not test every permutation, different option IDs, or open-ended numeric
answers. Adding an explicit instruction cost tokens without ensuring correctness.

### Longer object tracking

Six configurations use 4, 12 or 32 chronological events, mixing actual key
movements with visits that do not move it. All **54/54** answers were correct.
This extends the short tracking result to a longer sequence, but still uses a
single tracked object and simple chronological statements. It does not establish
performance with several interacting objects or out-of-order narration.

## Which hypotheses survived?

| Hypothesis | What the evidence supports |
|---|---|
| Jev cannot do elementary logic | Not supported by the revised 576/576 conditional panel or eligible pilot logic results. Scope is short, explicit rules. |
| Generic evidence-only instructions reliably improve answers | Not supported: no improvement at the pilot ceiling; counting unchanged overall; multi-step arithmetic lower. |
| Reversing choice order is harmless | Not supported for multi-step arithmetic; the matched reversal had substantially fewer correct selections. |
| Irrelevant numbers always break arithmetic | Not supported: simple arithmetic stayed perfect. Harder math showed more errors with distractors, especially under reversal. |
| Spacing fixes letter counting | Not supported: a small aggregate improvement coexisted with persistent errors and regressions. |
| Middle placement necessarily degrades retrieval | Not observed in the structured lookup panel; no conclusion about other retrieval tasks. |
| Explicit prerequisite questions transfer beyond car washing | Supported on four new object/service pairs with supplied physical-presence rules; not a full planning guarantee. |
| Repeated identical answers establish correctness | Not supported: stable wrong counts and the 242 arithmetic answer show the difference. |

Across the follow-up, 310/318 conditions returned the same selected answer in
all three repetitions. Stability therefore should not be confused with accuracy.
The remaining eight conditions varied; three repetitions cannot estimate their
long-run response distributions precisely.

## Practical interaction guidance

Use Jev's structured choices for narrowly defined questions with explicit facts,
constraints and unambiguous answer meanings. For uncertain propositions, define
`yes`, `no`, and `cannot_be_determined` as truth status rather than mixing truth
status with “does it follow?” entailment wording. The revised logic result
supports that tested prompt package; it does not prove each part is necessary.

For decisions, distinguish verifying requirements from choosing an action.
The original study found that correct prerequisite answers can coexist with a
wrong direct travel choice. Describe what each action actually does, check its
necessary conditions, and validate the final selection. The present extension
supports asking explicit condition questions; it does not validate an end-to-end
multi-call planning system.

For character counts and arithmetic, use deterministic code or a calculator to
compute or verify the result. Neither spacing, a cautionary prefix, confidence,
nor several identical answers provided a dependable substitute here. If a model
must select among computed outcomes, treat option order as an evaluation factor:
try matched permutations rather than trusting one favorable ordering.

Keep context relevant when possible. Record lookup worked at tested sizes and
positions, but structured lookup should not be treated as proof of broad
long-document understanding. Do not infer the maximum supported context window
from the largest successful test.

There is no single best prompt proven across these tasks. The strongest practical
pattern is **make the requested condition precise, state the facts and answer
semantics explicitly, and independently verify exact operations and decisions**.
The “explicit” mode itself was not a general performance improvement.

## Token usage per question

Each new request contains exactly one question. The following are **per-question
means**, not totals. They include the complete API request's context, schema and
any provider-counted overhead, not just the visible sentence. Full exact values
for each individual trial are in the two `per_question.csv` files below. Reversal
had the same mean input/output counts as plain; the explicit prefix added 25
input tokens per request. Output means were unchanged by the prefix for every
scoring-eligible family. The excluded pilot conditional family changed from
42.50 to 42.83 output tokens per question.

### Pilot

| Skill | Mean input tokens/question, plain | Mean input tokens/question, explicit | Mean output tokens/question, plain | Mean output tokens/question, explicit |
|---|---:|---:|---:|---:|
| arithmetic | 371.00 | 396.00 | 50.17 | 50.17 |
| conditional | 348.50 | 373.50 | 42.50 | 42.83 |
| decimal | 340.83 | 365.83 | 38.00 | 38.00 |
| evidence | 338.00 | 363.00 | 43.33 | 43.33 |
| negation | 335.00 | 360.00 | 42.00 | 42.00 |
| object tracking | 361.50 | 386.50 | 47.50 | 47.50 |
| ordering | 350.17 | 375.17 | 47.50 | 47.50 |
| prerequisite | 359.00 | 384.00 | 42.00 | 42.00 |
| quantifiers | 343.88 | 368.88 | 43.50 | 43.50 |
| retrieval | 3202.67 | 3227.67 | 60.00 | 60.00 |

The conditional row is retained here for accounting only, despite its scoring
exclusion. Pilot per-question input counts ranged 334–7,041; output 38–60.

### Follow-up

| Skill | Mean input tokens/question, plain | Mean input tokens/question, explicit | Mean output tokens/question, plain | Mean output tokens/question, explicit |
|---|---:|---:|---:|---:|
| conditional truth | 394.00 | 419.00 | 43.00 | 43.00 |
| exact count | 415.38 | 440.38 | 80.00 | 80.00 |
| long tracking | 581.33 | 606.33 | 47.50 | 47.50 |
| multistep math | 386.67 | 411.67 | 52.67 | 52.67 |

Follow-up per-question input counts ranged 365–850; output 42–80. Choice-set size,
answer serialization and supplied context differ between families, so differences
in token counts are not direct measures of reasoning effort.

## Evidence and reproduction

- [Pilot manifest and exact questions](results/20260916T083425766606Z-everyday-study/manifest.json)
- [Pilot raw responses](results/20260916T083425766606Z-everyday-study/results.jsonl)
- [Pilot per-question usage and scores](results/20260916T083425766606Z-everyday-study/per_question.csv)
- [Follow-up manifest and exact questions](results/20260916T085918297474Z-reasoning-followup/manifest.json)
- [Follow-up raw responses](results/20260916T085918297474Z-reasoning-followup/results.jsonl)
- [Follow-up per-question usage and scores](results/20260916T085918297474Z-reasoning-followup/per_question.csv)
- [Offline analysis](analyze_everyday_study.py), [label tests](test_everyday_study.py),
  [repository-wide verifier](verify_results.py), [report generator](build_everyday_report.py)

Run `python -m unittest -v test_everyday_study` and `python verify_results.py`
without an API key. To regenerate metrics, run `python analyze_everyday_study.py`
with either run directory, then `python build_everyday_report.py`. Running the
study scripts without `--plan-only` makes new paid API requests; reproducing a
prompt does not guarantee the same future responses or backend behavior.

The full repository now preserves **9,596 successful requests and 11,071 answers**,
plus the two original failed startup attempts. The larger answer count reflects
multi-question requests in the earlier study. Scoring exclusions do not remove
requests from this evidence inventory.

## Limitations and unresolved questions

These are small, manually chosen synthetic families with many shared templates,
not representative samples of everyday questions. Several tasks state the
constraints or semantic conventions explicitly. Multiple-choice answers expose
candidate solutions and may behave differently from free-form outputs. The
follow-up is adaptive and its findings need independent replication.

All observations concern one reported model version and one hosted API over
short collection intervals. We did not inspect model weights, training data,
server-side prompts, stochastic settings or cache behavior. No statement about
an internal behavioral “rule” is established as an architectural fact.

We have not measured deep logical composition, contradictory evidence, adversarial
instruction handling, multi-object tracking, free-form numeric generation,
long natural documents, or the exact context boundary. The next useful tests
would randomize every answer position, add unseen arithmetic templates, isolate
individual wording changes, and measure complete decision workflows. These are
proposals, not results included in the current pass counts.
