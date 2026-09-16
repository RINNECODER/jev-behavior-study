# Jev explicit car wash repetition test

Exact question:

> I need to wash my car. The car wash is a 5-minute walk from my home. Should I walk or drive there?

Run `python carwash_explicit_benchmark.py` for 1,000 separate requests with
four concurrent workers. Uses `TYPESAFE_API_KEY` from `.env` or the environment.
The question above is the complete instruction, with no appended text.
Choice schema: `walk: Walk`, then `drive: Drive`. Each input has empty state,
no history, no previous answers, and no hints. No batches or retries.

## Results: 2026-09-16

Run: `results/20260916T062850292266Z-carwash-explicit/`.
All 1,000 responses returned model `jev-1.13.0`.

| Answer | Count | Percent |
|---|---:|---:|
| Walk | 1,000 | 100% |
| Drive | 0 | 0% |
| Invalid or request error | 0 | 0% |

Expected answer: drive, because the car must be brought to the car wash.
Accuracy under that interpretation: 0%.

Verified 1,000 unique trial IDs, identical payload hashes, exact question,
empty state, all HTTP 200 responses, and raw answer counts. Reported input
usage: 327,000 tokens.

Inputs are isolated. Provider-side containers, caching, hidden context,
sampling, and statistical independence cannot be verified. Option order is
fixed. These results apply to the exact question and schema used here.
