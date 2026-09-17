# Verification receipt

- Frozen protocol/corpus and stage-selection commits precede their respective
  model calls. Policies were not tuned after held-out results.
- Four new policy tests plus fifteen existing engine/oracle/controller tests
  pass. New tests cover absence of quality-function calls, three options even
  at a corner, invertible coordinate transforms, own-proposal-only review, and
  no fallback when review fails.
- 640 screening decisions and all 64 development/held-out game trajectories
  verified by rebuilding exact payloads, hashes, raw responses and state changes.
  Every executed action equals the final model choice after command decoding.
- Offline shortest labels are separate from runtime records. No unknown shortest
  labels occurred on the final 48 games. The runner never invokes the scorer.
- 6,394 valid calls and two HTTP 529 failures retained; per-question input/output
  usage is exact for successful responses and unknown for failed requests.
- Chromium checks: default prose profile, 48 replays, step, seek, play/pause,
  best-run selection, JSON export, controller switching and URL restoration.
- Interrupted-game replay displays no executed move and unknown tokens; it does
  not display zero-cost/no-call success for the failed request.
- Real live prose decision verified: 538 input / 38 output tokens, no correction
  and no offline score provided in the live request. This QA call is excluded
  from study totals and stored under the ignored live-log directory.
- Desktop 1505×1045 and mobile 390×844 inspected visually; no horizontal page
  overflow. The viewer reuses the existing Snake Lab layout and palette.

[Verified desktop preview](preview.png). The complete per-question CSVs and raw
records are linked in [the report](REPORT.md). The follow-up's artifact hashes
are in `VALIDATION.json`; previous study snapshots remain separate.
