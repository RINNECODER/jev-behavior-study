# Demo verification

## Functional checks

- Nine Python tests pass: seeded/connected boards, relative turns, growth,
  wall/wrap behavior, vacating-tail legality, self/obstacle collision,
  termination, explicit guard assistance and deterministic baseline replay.
- Every published move in 105 study episodes is verified by `analyze.py` against
  regenerated state and the saved payload/response. There are 4,833 successful
  recorded model requests and one interrupted HTTP-error attempt across pilot,
  main and endurance runs. The error's usage/status/body are unknown.
- All 102 main/endurance replays are present in the exported browser dataset;
  pilot games remain separate raw evidence.
- Chromium interaction checks passed: step, seek, play/pause, difficulty switch,
  controller switch, best-run selection, and a real live Jev step (706 input
  tokens). Live QA is outside the frozen experiment totals.
- Share URLs preserve difficulty/controller/run. Export downloads the selected
  replay. Endurance records carry a separate phase label and higher-cap note;
  only main-run metrics populate the table.

## Browser and visual checks

No Browser/IAB tool was exposed in this session, so verification used the
installed agent-browser skill's Chromium automation. The concept was generated
with the built-in Image Gen tool. The game, controls, text, metrics and replay
are implemented as HTML/CSS/JavaScript, not a screenshot.

[Design reference](design-reference.png) · [Rendered desktop preview](preview.png)

The generated concept and final desktop/mobile screenshots were inspected with
`view_image`. Desktop viewport: 1505×1045, matching the concept dimensions;
full-page capture includes the added disclosure below the primary screen.
Mobile viewport: 390×844. No horizontal overflow or off-screen buttons.

## Fidelity and intentional adjustments

| Comparison | Verification / resolution |
|---|---|
| Composition | Preserved serif headline, square board on the left, controls/decision inspector on the right, results below. Mobile stacks these in reading order. |
| Palette | Preserved off-white paper, forest-green board, lime snake and coral food; grid lines remain readable. |
| Typography | Preserved editorial serif hierarchy with compact sans-serif form values. Fixed mobile latency wrapping by reducing metric type size and preventing numeric wrapping. |
| Controls | Functional play, step, timing selector, scrubber, selectors and per-move inspector match the concept's roles. Added live/replay tabs, download and best-run actions for the actual requested workflow. |
| Board | Intentional code-native square cells and eyes preserve exact collision alignment. No illustrated asset is substituted for the data. The true square board produces a taller page than the concept's slightly rectangular illustration. |
| Data / copy | Replaced concept dashes with measured data. Added forced-move, interrupted-run, target/cap and main-versus-endurance disclosures. Main title and subtitle match the reference. No invented performance numbers. |
| Responsive layout | Preserved board aspect ratio; transport controls wrap into two rows on mobile; table remains readable at 390px. |

Above-the-fold copy was checked against the concept. Intentional additions are
Live, best-run/download controls, actual seed/outcome labels, and latency/token
values from saved evidence. No marketing claims or unrelated navigation were
added. Implementation was visually verified against the concept with these
functional/scientific adjustments; there are no remaining known material visual
mismatches in the inspected views.

## Architecture

The viewer is deliberately a dependency-free static deliverable for GitHub Pages
and local opening. Local live mode is a standard-library Python server bound to
127.0.0.1. It keeps the key server-side, validates settings, serializes each game's
moves, rejects stale frames, and records calls locally. Public-host live controls
explain how to run the local server; public playback never calls Jev.
