# City lab — frozen pilot protocol v2

This is a small synthetic driving benchmark, not evidence of real-world driving ability. The car has continuous position, heading and speed in a 3D rendered grid city; physics are planar, simplified bicycle dynamics. The same engine.mjs runs browser and Node. No physics engine, realistic tire model, pedestrians, weather or sensor noise. Six scripted traffic cars obey lights and use a simple longitudinal following rule, but are not intelligent traffic agents. Collision bodies use approximate 1.8m-radius circles; curb detection uses a road-union margin. Rendering is illustrative, not a validated sensor simulator.

## Hypotheses, before API testing

H1: Direct steering/pedal control will be more difficult than choosing maneuvers backed by a lane controller. Assistance is a confound, not proof of stronger model reasoning.
H2: Real-time runs will accumulate errors because the previous command remains active during request latency; paused runs remove this source of state staleness.
H3: Destination and delivery tasks will expose routing and stopping failures that a survival-only task hides.
These are hypotheses. A 12-run pilot cannot prove them, estimate reliable success rates or isolate timing from nondeterministic model responses.

## Frozen pilot matrix

Seed 42 × three challenges (destination, explore, delivery) × two controllers (direct, maneuver) × two clocks (realtime, paused): 12 episodes. Order is deterministic and logged. Each episode ends at first collision, task completion, 90 simulated seconds, 160 decisions or API error. The decision cap is a resource limit and separately censored, not a model error. No retries or replacement of failed episodes. Two questions per decision, each in its own request, launched in parallel against the identical observation. This preserves **actual input/output usage for each question**, not an estimated split of request totals. No across-request conversation or previous episode context; previous controls are explicit state, not hidden history.

Direct: Jev chooses one of five steering levels and one of three pedal modes. No safety guard, action ranking, model correction, route search, emergency braking or fallback. Bounded mapping is the published action space.

Maneuver: Jev chooses north/east/south/west/stop and 0/4/8 m/s target speed. Code executes lane centering, turns near junctions and speed tracking. That is substantial assistance. Code does not choose destinations, plan a route, stop for red lights or avoid traffic. Labels must disclose assistance. Model commands during a turn update speed; the turn finishes before a new direction is executed.

Observations: structured simulator telemetry, known road grid, vehicle position/heading/speed, upcoming intersection geometry and light state, traffic within 55m, destinations and previous controls. These are engineered measurements, not perception by Jev. No recommended action, computed safe action, shortest route or collision forecast is supplied. Both techniques use the same state. Full public screenshot capture is available; native image driving is **unavailable pending a verified image API**, not scored as failure.

## Timing contract

Physics step 50 ms. Minimum observation interval 600 ms. Paused: world frozen during API wait, then execute the new action for 600 ms. Real time: world, lights and traffic advance with elapsed monotonic wall time while calls are pending; previous action remains active. New action takes effect when both replies arrive. At least 600 ms between observation captures. No concurrent decisions in a single episode. First pending action is neutral. Record wall latency, observation simulation timestamp, application simulation timestamp and their difference. Node advances the exact number of elapsed fixed ticks; browser retains accumulated time (no silent delta clamp) and stops if its tab becomes hidden, labeling interruption. Render interpolation is visual only. A failure or invalid response terminates without fallback. A reply arriving after the episode ends is logged but never applied.

## Outcomes and interpretation

Destination: stop within 6m of (58, 3.5), speed below 2m/s. Delivery: stop at all three ordered destinations. Explore: at 90s, at least 150m and two distinct intersections. Report completion and **clean completion** (zero red-light entries and zero speeding time), distance, stops, collisions, signal violations, speeding seconds, exploration coverage, decision count, calls, latency and per-question usage. First collision terminates. Road departure is classified curb collision; leaving map is also failure. No composite score or claim of optimal route. Efficiency: distance and elapsed time are observable, but no optimum is certified. Zero/100% in a tiny pilot is never a guarantee.

## Vision evidence

TypeSafe's documented System One interface uses a state and typed questions. We have not verified native image input for jev-1.13.0. Screenshot generation is not image understanding; an external OCR/vision pipeline would be a separate assisted technique. Sources: https://docs.typesafe.ai/introduction/quickstart and https://docs.typesafe.ai/primitives . See README for the API schema check and final pilot evidence.

## Reproduction

From repository root: `python3 city_demo/server.py`. In another terminal: `cd city_demo && node --test test.mjs`, then `node benchmark.mjs records/pilot-v2`. Requires server-side TYPESAFE_API_KEY (root ignored .env is loaded), Python 3 and Node 20+. Pilot generates at most 3,840 paid calls; actual cap 12 × 160 × 2. Stop on errors, retain all evidence. Browser live runs default to the same 160-decision cap. Run small integration verification before the pilot; mark it separately and exclude from pilot denominators.


## Amendment before pilot v2

Pilot v1 is retained in records/pilot-v1 with its source snapshot and original hashes. All 12 episodes collided. Inspection found rear-end impacts: traffic never responded to a slower ego vehicle. This confounds the apparent real-time disadvantage and is an environment limitation, not clean evidence of a model fault.

V2 changes only environment traffic: a car slows for a leader within 20m along its lane (including ego), using projected leader speed and a 7m following gap; traffic accelerates at 2m/s² and brakes at up to 7m/s². It also approaches red stop lines gradually. These rules never change ego actions. Prompts, seed, challenges, model, ego physics and controller mappings are unchanged. Separate complete 12-episode matrix; do not pool v1/v2. Added tests verify an idle ego is not rear-ended in its initial lane and both assisted turn directions clear the curb. This is a development amendment, not a held-out confirmatory trial.


Documentation correction after the pilot: collision circles are approximate, not conservative at every angle relative to the 1.9m × 4m rendered car. The frozen pre-run wording and unchanged simulator source are retained in records/pilot-v2/source.
