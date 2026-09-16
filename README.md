# Jev behavior study

An independent, AI-assisted investigation of **Jev 1.13.0**: how wording,
context placement, answer descriptions, prerequisite questions, and text
length affect its structured decisions.

**[Read the latest decision and limits report](DECISION_AND_LIMITS_REPORT.md)** ·
**[Read the original report](JEV_BEHAVIOR_REPORT.md)** ·
**[Read the new everyday reasoning report](EVERYDAY_REASONING_REPORT.md)** ·
[Main study evidence](results/20260916T075659560245Z-behavior-study/) ·
[Follow-up evidence](results/20260916T080433683304Z-behavior-followup/)

The report covers **2,805 new requests across 251 configurations**, plus five
earlier 1,000-request tests. The new extension adds **1,791 requests** testing
logic, arithmetic, counting, tracking, prerequisites and retrieval. The decision/order/limits study adds another **2,025 requests**. All **11,621
successful requests** are preserved.
Two failed startup attempts are included separately and produced no answers.
Inputs are synthetic; outputs are recorded live API responses from September
16, 2026. This is not an official TypeSafe benchmark or a representative
measurement of general model ability.

## Latest decision, order and limits findings

- Direct, descriptive and live two-step decisions each passed 288/288 on the
  same 48 new scenarios. The pipeline cost more and showed no accuracy gain
  on this ceiling panel; no incorrect prerequisite occurred.
- Every permutation of four arithmetic choices was tested. Correct-first
  accuracy was 95/108 versus 62/108 for correct-last.
- Regular logic chains passed through 32 links. Scrambled/broken-chain
  accuracy fell from 12/18 at eight links to 6/18 at 128.
- Dispersed highest-version records failed at middle positions: 1/6 with 512
  other records and 0/6 with 1,024. Start/end remained 6/6 in each cell.
- Carry/drop tracking exposed failures without a monotonic object-count limit.

See the [full report](DECISION_AND_LIMITS_REPORT.md),
[frozen and adaptive protocols](LIMITS_PROTOCOL.md), exact prompts, raw responses
and per-question token logs. These are task-specific findings, not universal
model thresholds.

## Earlier everyday reasoning extension findings

- Explicit conditional truth-status questions passed 576/576 requests across
  eight rule templates; structured retrieval passed 243/243 up to 512 records.
- Exact character counting passed 117/216. Spacing and generic evidence-only
  instructions did not make it reliable.
- Multi-step arithmetic passed 72/108. Reversing choices reduced its matched
  result from 29/36 to 18/36; irrelevant numbers also affected performance.
- The report discloses and excludes a 72-request pilot family with ambiguous
  grading semantics. All raw responses and original automatic scores remain.
- Both new runs include a `per_question.csv` with exact input/output token usage
  for each question, and offline label and evidence verification.

See the [research protocol](EXTENSION_PROTOCOL.md) for sources, hypotheses,
matched controls, limitations and reproduction commands. These are original
synthetic tests, not official benchmark scores.

## Original findings

- On 12 balanced travel scenarios, direct choices were correct in 65/120
  requests (54.2%); two explicit prerequisite checks were jointly correct in
  110/120 (91.7%). These are different output tasks, not interchangeable
  accuracy measurements.
- Descriptive action choices reached 225/240 correct choices on reused
  scenarios and 148/160 on eight additional scenarios, with documented
  failures and option-order effects.
- In one car-washing scenario, changing “5-minute walk” to “5-minute drive”
  changed correct choices from 0/20 to 20/20.
- Long-context prerequisite checks passed 196/200 requests with up to 8,192
  added filler words. Direct choices failed even without filler.
- High confidence was not a correctness guarantee. Exact letter counting
  remained unreliable across the tested strings and prompt variants.

The report documents failed hypotheses, confounders, adaptive follow-up
design, and the limits of repeated synthetic examples. It does not claim to
prove the model's internal reasoning mechanism.

## Scope

This is a **standalone repository**, assembled from an explicit file allowlist.
It contains only this report, its benchmark and analysis scripts, and selected
supporting evidence. It does not include the original workspace, API keys,
unrelated market experiments, or the proprietary runtime used for a local
interactive preview. The Markdown report is the portable published artifact.

## Inspect the data without making API calls

Python 3.10+; standard library only. No installation or API key is needed:

```bash
python verify_results.py
python analyze_behavior_study.py results/20260916T075659560245Z-behavior-study
python analyze_behavior_study.py results/20260916T080433683304Z-behavior-followup
python build_behavior_report.py
```

`verify_results.py` reconciles saved raw responses, schedules, payload hashes,
selected answers, request totals, and input/output tokens. Analysis commands
regenerate derived files locally. The report generator creates Markdown and
has no dependency on the original local report application.

Each new-study directory contains:

| File | Contents |
|---|---|
| `manifest.json` | Exact input payloads, expected labels, factors, repetitions |
| `schedule.json` | Randomized request order |
| `results.jsonl` | Raw API bodies, parsed responses, timestamps, scoring |
| `completion.json` | Planned/completed request counts and errors |
| `analysis.json` | Verified condition results and comparison tables |
| `conditions.csv` | One row per configured condition |
| `answers.csv` | One row per individual answer |

Expected answers are scoring metadata, **not** text sent to the model.

## Run fresh benchmarks

These commands call a paid external API. Each creates a new timestamped
results directory; it does not overwrite the published runs. Results can
change with provider behavior or model availability.

```bash
cp .env.example .env
# Edit .env locally and set TYPESAFE_API_KEY.

# Review the planned workload before sending requests:
python behavior_study.py --plan-only
python behavior_followup.py --plan-only

# 2,025 requests, then 780 requests:
python behavior_study.py
python behavior_followup.py
```

Alternatively, set `TYPESAFE_API_KEY` in your shell environment. Never commit
the key. The two study scripts pin `jev-1.13.0`, use four workers by default,
and do not automatically retry requests.

The individual tests each default to 1,000 requests and support `--count` and
`--workers`:

```bash
python flat_earth_benchmark.py
python carwash_benchmark.py
python carwash_explicit_benchmark.py
python carwash_decomposed_benchmark.py
python straberry_benchmark.py
```

Most original scripts request `jev-latest`; saved responses identify the
actual returned model. The decomposed test and the two new studies explicitly
request `jev-1.13.0`.

## Token usage

Token counts are provider-reported. Per-request usage includes every question
in that request; it is not separately attributed to each question in a batch.
The report and condition tables show per-request figures. Across all 7,805
successful recorded requests: **5,036,368 input tokens** and **420,305 output
tokens**. Missing usage for failed attempts is unknown, not an assumed zero.

## Reproducibility limits

Fresh request inputs do not guarantee provider-side independence or absence
of caching. Repeated requests are not independent new tasks. The second
study was designed after inspecting the first. The travel labels are
author-assigned, and the long contexts use repeated filler rather than a
representative natural-document corpus. Read the report before generalizing
its conclusions.

## License

[MIT](LICENSE) applies to the repository's authored code, report, and included
data to the extent the contributors hold rights. It does not grant rights to
Jev, TypeSafe software, model weights, trademarks, or linked third-party
documentation. No model weights or third-party report runtime are included.
