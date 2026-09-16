# Jev car wash prerequisite questions

Context supplied in `state`:

> I want to have my car washed at a car wash located a 5-minute walk from my home.

Both questions were sent together in every request:

- A: Does my car need to be physically present at the car wash to be washed there?
- B: If I walk to the car wash and leave my car at home, will that accomplish my goal of getting my car washed there?

Each choice schema, in order: `yes: Yes`, `no: No`,
`cannot_be_determined: Cannot be determined`. These descriptions and the A/B
field names are our concrete implementation of the supplied setup; the other
person's original full request JSON was not provided.

## Results: 2026-09-16

Run: `results/20260916T072813467567Z-carwash-decomposed/`.
Requested and returned model: `jev-1.13.0`.

| Measure | Result |
|---|---:|
| A selected yes | 1,000/1,000 (100%) |
| B selected no | 1,000/1,000 (100%) |
| Both correct in the same request | 1,000/1,000 (100%) |
| Invalid answers or request errors | 0 |
| Input tokens per combined request | 441 |
| Output tokens per combined request | 81 |

Token usage was identical in every response. The API does not separately
attribute tokens to A and B. Per-question mean confidence and option scores
are saved in `summary.json`; pass rates are based on selected answers.

Run `python carwash_decomposed_benchmark.py` to repeat. There are four concurrent
workers, a fresh HTTP opener per request, no cookies or cross-request history,
and no automatic retries. Both questions share the supplied context within
each request. Expected answers were recorded before the run. Verified all raw
answers, usage fields, HTTP statuses, model names, unique trial IDs, and payload
hashes. Offline checks also covered the runner's single-question compatibility,
joint grading, and incorrect/missing-answer handling.

This confirms repeatable success on these explicit prerequisite questions,
compared with 0/1,000 drive selections in the earlier direct-choice test.
It does not establish why the earlier test failed, nor demonstrate a correct
walk/drive selection. Several input features differ between the tests.
Provider-side caching, hidden context, and statistical independence cannot
be verified; option order is fixed.
