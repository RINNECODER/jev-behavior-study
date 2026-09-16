# Jev carwash repetition test

Exact prompt:

> I'm going to the carwash and it's really close, should I walk or should I drive? Answer only walk or drive.

Run `python carwash_benchmark.py` for 1,000 separate requests with four
concurrent workers. Requires `TYPESAFE_API_KEY` in `.env` or the environment.
Uses the shared runner in `flat_earth_benchmark.py`.

Each request supplies empty state and one choice question, with options
`walk: Walk` and `drive: Drive` in that order. No extra hints, conversation,
previous answers, or trial identifiers are included in the model input.
Each request uses a fresh HTTP opener with no cookie storage. No automatic
retries or batches are used. This provides input isolation, not separate
provider containers or proof of statistical independence; server caching,
sampling, and hidden context cannot be verified.

## Results: 2026-09-16

Run directory: `results/20260916T061211458188Z-carwash/`.
All 1,000 responses identified the model as `jev-1.13.0`.

| Answer | Count | Percent |
|---|---:|---:|
| Walk | 995 | 99.5% |
| Drive | 5 | 0.5% |
| Invalid or request error | 0 | 0% |

If the intended purpose is washing one's car, drive is the appropriate
answer because the car must be brought to the carwash. Under that
interpretation Jev answered correctly 0.5% of the time. The prompt implies
that purpose but does not explicitly state it. This result applies to the
exact wording and fixed option order tested, not all variants of the puzzle.

Verified 1,000 unique local trial IDs, identical payload hashes, empty state,
all HTTP 200 responses, and counts independently recomputed from saved raw
responses. Reported input usage: 327,000 tokens.
