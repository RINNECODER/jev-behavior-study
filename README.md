# How does Jev behave?

**A browsable field guide to Jev 1.13.0:** where explicit questions work, where
small changes alter answers, and where harder tasks expose failures.

**11,621 successful requests** · **13,096 answers** · **3 detailed reports**

Live API observations from September 16, 2026. Independent, AI-assisted research.

[Explore findings](#explore-the-findings) · [How to interact with Jev](#what-this-means-for-using-jev) · [Tokens per question](#tokens-per-question) · [Inspect the evidence](#inspect-the-evidence) · [Reproduce](#reproduce-the-study)

> **The central finding:** performance depends on the exact task and framing.
> Correct prerequisite answers do not always produce correct decisions, and
> passing a simple task does not establish reliability on a harder version.
>
> These are synthetic, task-specific results—not an official benchmark or an
> overall model score. Repeated calls are not independent new problems.

## Explore the findings

**Choose a question below, then expand its evidence.** Counts are correct
answers / requests unless explicitly labeled otherwise. Comparisons across
rows involve different tasks and should not be treated as one leaderboard.

| What do you want to know? | What we observed | Explore |
|---|---|---|
| Does breaking a decision into steps help? | All three methods tied at **288/288** on a new decision panel; two steps cost more. | [Decision methods](#1-does-a-two-step-decision-workflow-help) |
| Does answer order matter? | Arithmetic: **95/108** correct when the answer was first; **62/108** when last. | [Answer order](#2-can-answer-order-change-the-result) |
| Can it follow logical rules? | Simple rules worked; scrambled chains and missing links exposed failures. | [Logic](#3-how-far-does-logical-reasoning-transfer) |
| Can it use long context? | Simple lookup passed; dispersed middle-position facts failed at larger sizes. | [Context](#4-what-happens-to-facts-in-the-middle) |
| Can it count letters and track objects? | Letter counting: **117/216**. Explicit object moves worked better than some carrying histories. | [Exactness](#5-what-about-counting-and-object-tracking) |
| What happened with the car wash? | Explicit prerequisites passed even when the direct travel choice failed. | [Original puzzle](#6-what-started-this-the-car-wash) |

### 1. Does a two-step decision workflow help?

<details open>
<summary><strong>Expand: same 48 scenarios, three decision methods</strong></summary>

Twelve objects/services—such as laptop repair and camera cleaning—each had four
visit purposes. Half required bringing the item from home; half required going
without it. We tested both choice orders and three repetitions.

| Method | Final decisions correct | Mean input tokens per completed decision | Mean output tokens per completed decision |
|---|---:|---:|---:|
| Purpose-focused direct question | 288/288 | 365.81 | 32.50 |
| Descriptive action choices | 288/288 | 387.31 | 32.50 |
| Check prerequisite, then choose | 288/288 | 808.63 | 74.50 |

The two-step row sums **two requests**. Its second call received Jev's actual
first answer, with no correction or expected-label leakage. Every prerequisite
answer was correct, so this run did **not** test recovery from a wrong check.

**Takeaway:** this panel gives no accuracy reason to pay for an extra step.
It also cannot establish that a pipeline never helps: the direct baseline was
already perfect and explicitly stated the visit's purpose.

[Read the full decision analysis](DECISION_AND_LIMITS_REPORT.md#1-comparing-complete-decision-methods) · [Inspect paired workflow costs](results/20260916T124845798330Z-decision-pipeline/workflow_usage.csv)

</details>

### 2. Can answer order change the result?

<details>
<summary><strong>Expand: all 24 permutations, with choice meanings held fixed</strong></summary>

Six arithmetic problems × 24 option orders × three repetitions = **432 calls**.
Each correct-answer position occurred equally often within each problem.

| Correct choice position | Correct | Accuracy |
|---|---:|---:|
| First | 95/108 | 88.0% |
| Second | 67/108 | 62.0% |
| Third | 64/108 | 59.3% |
| Fourth | 62/108 | 57.4% |

For **13 × 11 − 23 + 8**, Jev selected the correct **128** on 32/72 calls and
**120** on 40/72. The latter matches omitting the received eight items.
That describes the answer pattern; it does not reveal its internal calculation.

**Takeaway:** choice order is an evaluation variable, not harmless formatting.
Putting the answer first is not a reliability guarantee. Only six numerical
problems were tested, and option IDs were not independently counterbalanced.

[Read the permutation analysis](DECISION_AND_LIMITS_REPORT.md#2-all-answer-permutations-on-arithmetic) · [Inspect every payload and order](results/20260916T124604860296Z-limits-study/manifest.json)

</details>

### 3. How far does logical reasoning transfer?

<details>
<summary><strong>Expand: passing long regular chains concealed missing-link failures</strong></summary>

Short, explicitly defined conditional questions passed **576/576** in an earlier
panel. Regular one-way chains then passed **162/162**, through 32 links.

The harder follow-up scrambled category names and rule order, added a disjoint
chain, and removed a necessary link in the unknown cases.

| Underlying chain length | Necessarily true | Necessarily false | Missing-link unknown | Overall |
|---|---:|---:|---:|---:|
| 8 links | 6/6 | 6/6 | 0/6 | 12/18 |
| 32 links | 6/6 | 1/6 | 0/6 | 7/18 |
| 128 links | 6/6 | 0/6 | 0/6 | 6/18 |

**Takeaway:** test missing and negative evidence, not only successful forward
chains. This is not an absolute depth limit: forward-true cases still passed
at 128. Each cell contains just two generated instances, each repeated three
times; several structural changes separate the regular and harder panels.

[Read the difficulty analysis](DECISION_AND_LIMITS_REPORT.md#3-increasing-difficulty-regular-versus-harder-structure) · [Inspect the harder test generator](stress_followup.py)

</details>

### 4. What happens to facts in the middle?

<details>
<summary><strong>Expand: lookup success did not transfer to dispersed conflicting records</strong></summary>

Plain structured lookup passed **243/243**, up to 512 records. Grouped conflicting
records also passed **108/108** when the rule selected the highest version.

Next, we dispersed conflicting TARGET records through the text. The task was
still to select TARGET's highest version, regardless of mention order.

| Other records | Winner at start | Winner in middle | Winner at end | Input tokens per question |
|---|---:|---:|---:|---:|
| 128 | 6/6 | 6/6 | 6/6 | 2,182 |
| 512 | 6/6 | 1/6 | 6/6 | 7,558 |
| 1,024 | 6/6 | 0/6 | 6/6 | 14,726 |

All eleven errors selected version 3 instead of the winning version 4.

**Takeaway:** test position and conflicting evidence together. This narrow
highest-version task is not a natural-document benchmark, and 14,726 tokens
is a tested input size—not a measured maximum context window.

[Read the context analysis](DECISION_AND_LIMITS_REPORT.md#competing-records-and-middle-placement) · [Inspect per-question responses and usage](results/20260916T125040590877Z-stress-followup/per_question.csv)

</details>

### 5. What about counting and object tracking?

<details>
<summary><strong>Expand: exact characters and implicit state changes remain different skills</strong></summary>

**Letter counting:** twelve strings, contiguous/spaced formats, three prompt
modes and three repetitions yielded **117/216 correct**. `raven` has one `r`,
but all 18 tested variants/repetitions selected two. Spacing helped some items
and hurt others; a generic evidence-only prefix did not improve overall accuracy.

**Tracking:** explicit object moves passed **45/45** across 1–16 objects. The
harder task required inferring whether an object followed a person or stayed
where it was dropped:

| People and objects | Carry/drop questions correct |
|---|---:|
| 8 | 3/6 |
| 16 | 6/6 |
| 32 | 3/6 |

**Takeaway:** use deterministic code for exact counts. Tracking results show
specific failures, not a clean object-capacity threshold; the curve is not
monotonic and contains only two histories per size.

[Read the counting analysis](EVERYDAY_REASONING_REPORT.md#exact-character-counting) · [Read the tracking analysis](DECISION_AND_LIMITS_REPORT.md#object-count-versus-carrying-state)

</details>

### 6. What started this? The car wash

<details>
<summary><strong>Expand: knowing a necessary condition did not ensure the correct action</strong></summary>

> I need to wash my car. The car wash is a 5-minute walk from my home.
> Should I walk or drive there?

The original explicit direct-choice test selected **walk in all 1,000 calls**.
Under the ordinary intended scenario, the car needs to be brought to the wash.

Two explicit questions—whether the car must be present and whether walking while
leaving it home accomplishes the goal—were jointly correct in **1,000/1,000**
requests. In a later batch containing prerequisites **and** the travel question,
correct prerequisite answers still accompanied the wrong travel choice in all
25 calls. Batching is not the same intervention as a sequential pipeline.

A separate matched wording test changed “5-minute walk” to “5-minute drive”:
correct travel choices changed from **0/20 to 20/20**.

**Takeaway:** knowledge of prerequisites and action selection must be evaluated
separately. These results do not prove the reason for the earlier mistake, and
the later successful item-transport panel used different questions and scenarios.

[Read the original investigation](JEV_BEHAVIOR_REPORT.md) · [Inspect the original explicit test](carwash_explicit_benchmark.py) · [Inspect the decomposed test](carwash_decomposed_benchmark.py)

</details>

## What this means for using Jev

| When you need… | Practice supported by these observations | Important limit |
|---|---|---|
| A constrained decision | State the purpose and relevant conditions explicitly. | Successful explicit checks do not guarantee the final action. |
| A truth-status answer | Define true, false and unknown unambiguously. | “Not entailed” and “false” are different judgments. |
| An exact number or count | Compute or verify it with deterministic code. | Repetition, confidence and option placement do not ensure correctness. |
| A multiple-choice evaluation | Balance option positions and inspect per-item changes. | Aggregate accuracy can hide prompt-sensitive items. |
| A decision pipeline | Compare complete-workflow accuracy and token cost against a direct baseline. | The latest panel showed extra cost without a gain; bad-check recovery remains untested. |
| A long-context answer | Test fact position, competing records and the actual task structure. | A successful lookup test does not validate all document reasoning. |

## Tokens per question

**Exact usage is available for each question in the newer studies.** Every
request in these runs contains one question, so its reported input/output
usage is attributable to that complete request, including context and schema.

| Run | Per-question input/output usage |
|---|---|
| Everyday reasoning pilot | [Open CSV](results/20260916T083425766606Z-everyday-study/per_question.csv) |
| Counting and reasoning follow-up | [Open CSV](results/20260916T085918297474Z-reasoning-followup/per_question.csv) |
| Decisions, permutations and regular difficulty tests | [Open CSV](results/20260916T124604860296Z-limits-study/per_question.csv) |
| Pipeline final decisions | [Open CSV](results/20260916T124845798330Z-decision-pipeline/per_question.csv) |
| Harder logic, tracking and dispersed records | [Open CSV](results/20260916T125040590877Z-stress-followup/per_question.csv) |

[Paired pipeline costs](results/20260916T124845798330Z-decision-pipeline/workflow_usage.csv)
show each stage separately and explicitly label the two-request sums.
Older multi-question batches report usage for the whole request; individual
question costs cannot be recovered from those totals.

<details>
<summary>Expand repository-wide accounting</summary>

Across **11,621 successful requests**: **8,084,680 input tokens** and
**593,109 output tokens**, as reported by the provider. These are aggregate
inventory figures, not per-question costs or measures of reasoning effort.
Two failed historical startup attempts are preserved separately; their usage
is unknown, not assumed zero. Agent work used to conduct the research is not
included in Jev's usage figures.

</details>

## Inspect the evidence

| Investigation | Report | Protocol / exact tests | Saved runs |
|---|---|---|---|
| Car wash, wording and prerequisites | [Original report](JEV_BEHAVIOR_REPORT.md) | [Main suite](behavior_study.py) · [Follow-up](behavior_followup.py) | [Main](results/20260916T075659560245Z-behavior-study/) · [Follow-up](results/20260916T080433683304Z-behavior-followup/) |
| Everyday logic, counting and retrieval | [Everyday report](EVERYDAY_REASONING_REPORT.md) | [Protocol](EXTENSION_PROTOCOL.md) · [Pilot](everyday_study.py) · [Follow-up](reasoning_followup.py) | [Pilot](results/20260916T083425766606Z-everyday-study/) · [Follow-up](results/20260916T085918297474Z-reasoning-followup/) |
| Decision pipelines, permutations and limits | [Latest report](DECISION_AND_LIMITS_REPORT.md) | [Protocol](LIMITS_PROTOCOL.md) · [Main suite](limits_study.py) · [Pipeline](run_decision_pipeline.py) · [Stress tests](stress_followup.py) | [Main](results/20260916T124604860296Z-limits-study/) · [Pipeline](results/20260916T124845798330Z-decision-pipeline/) · [Stress](results/20260916T125040590877Z-stress-followup/) |

<details>
<summary>Which file answers which question?</summary>

| File | Use it to inspect… |
|---|---|
| `manifest.json` | Exact payloads, expected labels, factors and repetitions |
| `schedule.json` | Shuffled request order |
| `results.jsonl` | Raw API bodies, parsed outputs, timestamps and scores |
| `completion.json` | Planned/completed counts and transport errors |
| `analysis.json` | Verified condition-level results |
| `conditions.csv` / `answers.csv` | Conditions and individual answers |
| `per_question.csv`, where present | Exact input/output usage for each single-question request |
| `workflow_usage.csv`, pipeline run | Source/final pairing, stage costs and workflow sums |

Expected labels are scoring metadata, **not input sent to the model**.
The pipeline intentionally forwards the actual prerequisite choice, with its
source trial recorded for reconstruction.

</details>

<details>
<summary><strong>Read the caveats and the disclosed grading correction</strong></summary>

- These are manually designed synthetic families, often with shared templates.
  Repeated requests measure observed stability, not independent problem coverage.
- Some follow-ups were designed after earlier results. Protocols disclose this;
  the studies are not untouched external benchmark evaluations.
- **72 pilot conditional requests are excluded from substantive accuracy claims**
  because “Does it follow?” allowed a reasonable answer different from our
  intended truth-status labeling. All original outputs and automatic grades
  remain saved. [Read the correction](EVERYDAY_REASONING_REPORT.md#design-grading-and-an-important-correction).
- Every saved successful response identifies `jev-1.13.0`. That does not establish
  access to fixed weights, hidden prompts, server-side randomness or cache behavior.
- Reported confidence is not a correctness guarantee. No population calibration
  claim or internal reasoning mechanism is established here.
- Difficulty failures are task-specific; no absolute context, depth or object
  capacity was measured. Passing every trial in a small panel is not universal
  reliability.

</details>

## Reproduce the study

<details>
<summary><strong>Verify saved evidence offline — no API key or installation needed</strong></summary>

Python 3.10+, standard library only. From the repository root:

```bash
python verify_results.py
python -m unittest -v test_limits_study test_everyday_study
```

The verifier checks saved payload hashes, raw responses, selected answers,
schedules, request counts and token totals. The tests check labels, balanced
permutations, state simulation and pipeline forwarding.

To regenerate the latest analysis and report:

```bash
python analyze_limits_study.py \
  results/20260916T124604860296Z-limits-study \
  results/20260916T124845798330Z-decision-pipeline \
  results/20260916T125040590877Z-stress-followup
python build_limits_report.py
```

Analysis commands rewrite derived files locally; they make no API calls.
The other reports contain their own reproduction commands.

</details>

<details>
<summary>Run new live tests — makes paid API requests</summary>

Set `TYPESAFE_API_KEY` in your environment, or copy `.env.example` to `.env`
and edit it locally. Never commit credentials.

Inspect workloads without sending requests:

```bash
python limits_study.py --plan-only
python stress_followup.py --plan-only
```

Run the latest study:

```bash
python limits_study.py
# Substitute the new directory printed by the first command:
python run_decision_pipeline.py results/<new-limits-study-directory>
python stress_followup.py
```

This sends 1,611 main calls, 288 dependent final decisions, then 126 stress calls.
Each run creates a new timestamped directory. These suites pin `jev-1.13.0`,
default to four workers, and do not retry automatically. Future outputs may vary.

The original individual benchmarks—`flat_earth_benchmark.py`,
`carwash_benchmark.py`, `carwash_explicit_benchmark.py`,
`carwash_decomposed_benchmark.py`, and `straberry_benchmark.py`—default to
1,000 calls and support `--count` and `--workers`. Most request `jev-latest`;
the decomposed test pins `jev-1.13.0`. Saved responses identify the model returned.

</details>

## Scope and license

This is a standalone repository containing authored reports, tests and selected
evidence. It does not include the original workspace, credentials, unrelated
experiments, model weights or a proprietary report runtime.

[MIT](LICENSE) applies to the contributed code, reports and included data to the
extent the contributors hold rights. It grants no rights to Jev, TypeSafe
software, model weights, trademarks or linked third-party documentation.

[Back to the findings ↑](#explore-the-findings)
