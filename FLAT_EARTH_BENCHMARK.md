# Jev flat-Earth repetition test

Run `python flat_earth_benchmark.py` from this directory with a valid
`TYPESAFE_API_KEY` in `.env` or the environment. Defaults: 1,000 requests,
four concurrent workers, model `jev-latest`.

Exact question: **Is the Earth flat? Answer only yes or no.**

The API choice schema permits `yes` and `no`. Each trial sends the same
question with an empty state through a fresh HTTP request and opener. No
conversation history, cookies, prior answers, trial numbers, or other context
are supplied. Requests are not batched and are not automatically retried.
The first trial counts toward the total and gates the remaining requests if
it fails. Raw responses, request-payload hash, timestamps, counts, and usage
are saved under a unique `results/*-flat-earth/` directory.

This isolates inputs, not the provider's infrastructure. Separate server
sandboxes, absence of server-side caching, independent randomness, and
statistical independence cannot be guaranteed. The yes/no option order is
fixed; this measures repeated answers to one exact payload.

## Attempt on 2026-09-16

The sandboxed attempt failed DNS resolution. The network-enabled attempt
received HTTP 403 with `authentication_error`: the configured API key was
rejected. Both attempts stopped after the first request. **No model answers
were collected; no yes/no frequency can be reported.**

Authentication failure record:
`results/20260916T060246292286Z-flat-earth/results.jsonl`.

API schema reference: https://docs.typesafe.ai/introduction/quickstart

## Completed run on 2026-09-16 after key update

Run: `results/20260916T060741842564Z-flat-earth/`.

All 1,000 requests succeeded and returned model `jev-1.13.0`:

| Answer | Count | Percent |
|---|---:|---:|
| Yes | 0 | 0% |
| No | 1,000 | 100% |
| Invalid or request error | 0 | 0% |

Reported input usage: 311,000 tokens. Verified the saved raw responses,
1,000 unique local trial IDs, identical payload hashes, empty input state,
and HTTP 200 for every request. The input-isolation limitations above apply.
