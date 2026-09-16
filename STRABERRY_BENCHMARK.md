# Jev letter-count repetition test

Exact prompt, preserving the user's spelling:

> How many R's are in straberry? Answer only with the number.

Run `python straberry_benchmark.py` for 1,000 separate requests with four
concurrent workers. Requires `TYPESAFE_API_KEY` in `.env` or the environment.
The choice schema offers integers 0 through 10 in ascending order, with each
number's description equal to itself. Empty state, no conversation history,
no prior answers, no hints, no batching, and no automatic retries.

## Results: 2026-09-16

Run: `results/20260916T061553342213Z-straberry/`.
All 1,000 responses reported model `jev-1.13.0`.

| Answer | Count | Percent |
|---|---:|---:|
| 2 | 999 | 99.9% |
| 3 | 1 | 0.1% |
| Other answers, invalid answers, or errors | 0 | 0% |

The correct case-insensitive letter count is **3**: st**r**abe**rr**y.
Accuracy for this exact prompt and choice schema: **0.1%**.
This run tested `straberry`, not the standard spelling `strawberry`.

Verified 1,000 unique local trial IDs, identical request payload hashes,
empty state, all HTTP 200 responses, and counts independently recomputed
from raw saved responses. Expected count verified with Python string counting.
Reported input usage: 426,000 tokens.

Input isolation does not establish provider-side sandboxing, absence of
caching, or statistical independence. Option order was fixed and no sampling
controls were supplied. This is a constrained-choice test, not free-text
generation or a test of other word spellings.
