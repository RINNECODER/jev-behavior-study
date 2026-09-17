# City lab verification

## Functional evidence

Nineteen automated tests pass with Node: deterministic state, uncorrected direct actions, traffic and curb collisions, goal stopping threshold, red-light entries, all-red signal phase, identical observation/separate question calls, invalid actions, paused versus real-time waits, API errors, late responses, lane tracking, left/right turns at two speeds, environment following, and one reachable destination trajectory without traffic. That last trajectory is a calibration, not a clean traffic-obeying benchmark result.

`validate.mjs` independently replays all 24 published episodes (2,936 per-question call records) from raw response choices against the correct simulator version and checks final snapshots and events exactly. `analyze.py` verifies source hashes, episode configs, one question per call and zero paused observation age. Results and REPORT.md are rebuilt from those traces.

Browser/IAB was not exposed, so verification used agent-browser's Chromium fallback. Desktop: 1536 × 1024, matching concept dimensions. Mobile: 390 × 844. No horizontal page overflow. Browser error log empty during core checks. Public mode was tested by intercepting only the readiness response: live Jev disabled, manual available, native vision explicitly disabled. The interception was removed afterward.

Verified interactions: a live paused Jev integration run with separately displayed steering/pedal token counts; stop with pending response; keyboard acceleration and map-boundary collision; replay play/pause; seek to terminal frame (terminal collision visible); follow/map camera selection; real JSON download; real PNG capture; mode/seed/challenge controls; mobile layout and native select readability. Raw paid pilot integration is separate from the UI smoke run. Public recordings are genuine pilot traces, not generated demo choices.

## Design fidelity review

Reference: [generated full-screen concept](design/concept.png). System inventory: [SPEC.md](design/SPEC.md). Both concept and latest browser screenshots were opened with `view_image` in the same final comparison pass. Temporary screenshots and download checks remain outside the repository.

| Comparison point | Concept and implementation | Resolution |
|---|---|---|
| Composition | Wide left city, narrow right inspector, four-metric strip | Kept; adjusted header/title spacing and viewport height to align at native dimensions |
| Typography | Large serif heading and numeric metrics, restrained sans controls | Explicit type sizes/families; no browser-default button text |
| Palette | Off-white background, forest action/status, gray borders | Matched tokens; no added viewport tint or gradient |
| Copy | Title, description, field labels, start action and metric labels | Preserved; functional additions listed below |
| Container model | Open inspector rail, simple rectangular viewport, subtle metric frame | Kept; decision stream uses readable rows when populated |
| 3D asset treatment | Reference produced photoreal architecture despite low-poly brief | Intentional geometry deviation: actual mesh city supports moving cameras, collisions and screenshots; no raster city pretending to be a simulator |
| Mobile | Stacked extension of same system | Full-width fields on narrow screens fix truncated selections; no horizontal page overflow |
| Camera/framing | Following car on a boulevard | Lowered chase camera and enlarged visible vehicle; map camera is functional |

Above-the-fold copy audit: preserved all core reference strings. Necessary additions are connection availability, simulation clock, live waiting/terminal statuses and assistance descriptions. Below the first screen: recording selection, capture, comparison table and methodology disclosure implement requested research workflows. A clear native-vision availability label replaces an unsupported option. The reference's empty decision frame is an open rail in implementation so live question records have room.

The interface was verified against the design with the above deliberate differences. The city is intentionally low-poly rather than the concept's photoreal image. No unresolved clipping, mobile overflow, inert primary actions or unlabelled fake model data were found.
