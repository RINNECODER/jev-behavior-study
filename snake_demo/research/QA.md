# Verification receipt

- Frozen protocol, corpus and selected game schedule precede their model calls.
- Six oracle/controller tests and nine existing engine/controller tests pass.
- 924 diagnostic payloads, raw responses, labels and exact question token counts
  regenerated and verified; 120 corpus oracle labels recomputed.
- All 64 held-out games replayed against the engine, regenerated request payloads,
  response text, oracle costs/path witnesses and proposal/execution rules.
- 100 additional short code-only games and 16 original long code-only games
  replayed and verified. Planner errors remain visible, not scored as collisions.
- 32 bounded-certificate long games replayed; all successful certificates and
  paths recomputed. Terminal unknown budget records checked structurally rather
  than rerun. That limit is explicit in each verifier summary.
- V2 optimal-action sets matched original exact labels on all 120 frozen states.
- JavaScript syntax checked. Chromium: replay selection, step, seek, best-run,
  live mode and a real assisted Jev move verified. Live move was 563 input /
  38 output tokens, excluded from published experiment totals.
- Desktop (1505×1045) and mobile (390×844) screenshots visually inspected.
  No horizontal overflow on mobile. Existing Snake Lab visual design is reused;
  extra route costs and explicit proposal/execution labels explain assistance.
- [Rendered desktop preview](preview.png).

The legacy `snake_demo/VALIDATION.json` records the original experiment artifact
hashes at its publication commit; later documentation additions are expected to
change those documents. This follow-up's `VALIDATION.json` covers its own evidence
and viewer. Old raw game records were not rewritten.
