# Everyday reasoning extension protocol

These original, synthetic tests investigate behavior of the hosted `jev-1.13.0`
choice API. They are not an implementation of any published benchmark.

## Research basis

- [bAbI: prerequisite toy tasks](https://arxiv.org/abs/1502.05698) motivates
  separating fact chaining, deduction and other skills instead of reporting
  only one combined accuracy.
- [GSM-Symbolic](https://arxiv.org/abs/2410.05229) motivates numerical template
  variation and paired irrelevant-detail controls. This study does not infer
  internal reasoning mechanisms from either successes or failures.
- [Lost in the Middle](https://arxiv.org/abs/2307.03172) motivates varying target
  position in retrieval contexts. Our generated record lookup is narrower
  than real document comprehension.

## Design and hypotheses

The pilot contains 93 base items, 279 prompt conditions and 837 requests.
Every base item is presented with ordinary instructions, reversed choice order,
and an evidence-only instruction prefix. Each condition runs three times.
The matched variants preserve state, expected answer and choice meanings.
The manifest saves all exact payloads, labels, factors and hypotheses before
requests begin. A shuffled schedule interleaves conditions. Workers: four;
no retries, no response reuse, fresh HTTP opener, no conversation history.
No client-level isolation can establish that the provider uses independent
randomness, has no cache, or has no shared server-side state.

The pilot probes material implications, negation, quantifiers, small arithmetic,
decimal comparison, object tracking, temporal ordering, explicit prerequisites,
missing information/fictional facts, and record lookup. Arithmetic includes
paired irrelevant quantities. Retrieval crosses 16/128/512 records with
start/middle/end target positions and three code-offset samples. These are
structured records, not natural long documents.

Pilot hypotheses are in `everyday_study.HYPOTHESES`. The suite was frozen before
responses were collected; no failures were retried or removed from raw data.
However, review found a semantic problem in the conditional family's question
wording: "Does it follow that P?" allows "no" when P is not entailed, whereas
our original key used "cannot_be_determined" when P could be true or false.
The complete 72-request pilot conditional family is excluded from substantive
accuracy claims. Saved automatic scores remain untouched for auditability.
This is a labeling/prompt problem, not verified evidence of a model error.

## Adaptive follow-up

After viewing pilot responses, the follow-up was designed to resolve that
ambiguity and probe harder exact tasks. Its separately frozen manifest contains
106 base items, 318 conditions and 954 requests. There are eight conditional
rule templates, each with eight observation/query combinations. The question
explicitly defines yes as necessarily true, no as necessarily false, and
cannot_be_determined as both truth values remaining possible. It also states
that no converse rule is given. Thus this is a wording/package revision, not a
single-variable causal experiment.

Other follow-up tasks are twelve counting strings, each contiguous/spaced;
six multiplication/subtraction/addition problems, each with/without irrelevant
numbers; and key tracking across 4/12/32 events with two starting locations.
All use the same three modes and three repetitions. Counting includes ordinary
words, artificial strings, mixed case and underscores. Exact labels come from
Python character counting, integer/decimal arithmetic, event-state simulation
and truth-table enumeration. Offline tests independently parse selected prompt
families to check their labels and matched controls.

## Interpretation rules

Report selected choices, not the largest displayed probability. Include all
requests, transport failures and per-question input/output usage. One question
per request makes API token usage attributable to the whole typed question
request, including its context/schema/provider overhead; it does not measure
only the visible question sentence. Do not apportion hidden token costs.

Three repeated calls measure observed stability, not three independent problem
instances. Report base-item counts and distinguish unseen instances from reused
templates. No population pass rate, causal mechanism, calibrated confidence,
context-window limit, or statistical significance is established. Ceiling
results cannot establish that a prompt intervention improves ability. Adaptive
follow-up is disclosed and is not an untouched external test set.

## Reproduce

With Python 3 and `TYPESAFE_API_KEY` in the environment (or a local ignored
`.env`), run `python everyday_study.py --plan-only` or
`python reasoning_followup.py --plan-only` to inspect counts without API calls.
Remove `--plan-only` to make paid API calls. New runs receive new directories;
original evidence is never overwritten. Run
`python analyze_everyday_study.py results/<run-directory>` for offline analysis.
`python -m unittest -v test_everyday_study` checks construction and labels.
`python verify_results.py` audits all published evidence against frozen totals.
