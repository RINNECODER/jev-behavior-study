"""Render descriptive findings from the verified complete pilot, without inferring causation."""
from collections import Counter
from pathlib import Path
import json
import statistics

ROOT = Path(__file__).resolve().parent
v1 = json.loads((ROOT / 'records/pilot-v1/analysis.json').read_text())
v2 = json.loads((ROOT / 'records/pilot-v2/analysis.json').read_text())
assert v1['complete_matrix'] and v2['complete_matrix'], 'Wait for complete matrices'
completed = sum(r['status'] == 'completed' for r in v2['runs'])
clean = sum(r['clean_completion'] for r in v2['runs'])
rows = []
all_calls = []
for r in v2['runs']:
    d = json.loads((ROOT / 'records/pilot-v2' / (r['run'] + '.json')).read_text())
    all_calls.extend(c for decision in d['decisions'] for c in decision['result']['calls'])
    rows.append(f"| {r['run']} | {r['status']} | {r['sim_seconds']:.2f} | {r['distance_m']:.1f} | {r['stops']} | {r['red_lights']} | {r['speeding_seconds']:.2f} | {r['median_observation_age_s']:.2f} |")
usage = []
for q, group in v2['per_question'].items():
    cs = [c for c in all_calls if q in c['payload']['questions'] and c.get('response', {}).get('usage')]
    inputs = [c['response']['usage']['input_tokens'] for c in cs]
    outputs = [c['response']['usage']['output_tokens'] for c in cs]
    usage.append(f"| {q} | {group['calls']} | {statistics.mean(inputs):.1f} ({min(inputs)}–{max(inputs)}) | {statistics.mean(outputs):.1f} ({min(outputs)}–{max(outputs)}) | {group['median_latency_ms']:.1f} |")
steering = Counter(c['response']['answers']['steering']['choice'] for c in all_calls if c.get('valid') and 'steering' in c['payload']['questions'])
report = f'''# Jev City lab: exploratory driving results

The corrected pilot completed **{completed}/12 tasks**, with **{clean}/12 clean completions**. These are twelve specific episodes, one per condition, not a reliable estimate of general driving accuracy. The useful result is a reproducible set of failure traces and an explicit timing/control comparison. This study does not establish native vision, optimal routing, or real-world driving ability.

[Interactive viewer](https://rinnecoder.github.io/jev-behavior-study/city_demo/) · [Frozen protocol](PROTOCOL.md) · [Exact per-question usage](records/pilot-v2/per-question.csv) · [Machine-readable findings](records/pilot-v2/analysis.json)

## Experimental design

Pinned `jev-1.13.0`, traffic seed 42, three objectives (destination, exploration, three-stop delivery), two control techniques, two clocks. Each condition is one episode, ending on collision, completion, 90 simulated seconds, 160 decisions or API failure. Model requests have no conversation history. Two atomic questions see the same structured observation, each sent in its own request and launched concurrently. There is no across-episode context. API calls within an episode are correlated observations of one trajectory, not independent trials.

Direct mode asks for five-valued steering and three-valued pedal control. The supplied observations include the exact pose, speed, road grid, next signal and nearby traffic, but no action recommendation, route cost or safety verdict. This is unassisted **action selection from engineered telemetry**, not unassisted perception.

Maneuver mode asks for cardinal direction and target speed. Code tracks lanes, turns near junctions and controls speed; it does not plan a route or prevent collisions. Its extra controller, different action space and lower selectable speeds are confounds. Comparing these modes evaluates two systems, not the model in isolation. Questions are chosen independently; mutually awkward combinations are executed as documented, not silently repaired.

Real time advances physics, lights and traffic during the network wait, holding the previous control. Paused mode freezes the entire world during the request, then advances 0.6 seconds with the new control. The shared engine uses fixed 50 ms steps. Observation age measures simulated time between capture and action application; network latency measures wall time. Both are recorded separately. Browser replay runs at simulation speed and omits API wait duration; live real-time mode really does continue while waiting.

## Corrected pilot v2

| Condition | Outcome | Simulated seconds | Metres | Stops | Red-light entries | Speeding seconds | Median observation age, s |
|---|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

Every collision ends the episode. `curb_collision` includes leaving the map. Completion requires stopping within 6m and below 2m/s for destination/delivery; exploration requires surviving 90s, travelling 150m and visiting two distinct intersections. Distance alone is not success, and a longer failed trajectory is not necessarily better. No route-optimality score is reported because no optimal continuous trajectory has been certified.

## What the traces show

Across the direct-control calls in v2, steering choices were **{dict(steering)}**. Counts describe these prompts and trajectories only. In the destination direct-control runs, Jev continued along the northbound road instead of completing the turn toward the eastward destination. Pedal decisions changed while steering did not deliver the required route. The pauses and signal responses therefore do not establish successful navigation.

Assisted control did not establish reliable task completion either. Lane tracking can execute a supplied turn, as offline calibration tests demonstrate, but Jev still has to select a consistent route, choose when to stop and handle interactions. A high-level command followed by a collision does not by itself identify whether the decision, turn executor, traffic behavior or their interaction is responsible. The raw traces preserve the evidence needed to distinguish those cases.

H1 (maneuver assistance helps) is **not established by completion results**. H2 (real time hurts through latency) is **not established causally**: clocks change state timing, calls are stochastic, there is one seed and no controlled latency injection. H3 (route/stopping objectives expose failures hidden by distance) is supported only descriptively: vehicles can travel substantial distances without completing a required stop. None of these observations proves a general behavioral law.

## A simulator flaw we found and corrected

Pilot v1 produced 12 collisions in 12 episodes. Scripted traffic did not slow for a vehicle ahead. A faster following car started behind the ego car, so API startup delay and conservative model speed choices could cause a rear-end impact. That setup made real-time runs look especially weak for a reason partly imposed by the environment.

We retained [all v1 traces](records/pilot-v1/summary.json), their [analysis](records/pilot-v1/analysis.json), and [exact source snapshot](records/pilot-v1/source/). V2 adds a simple following rule to the **other cars**, plus gradual stopping at red lights. It never overrides ego controls. Both full matrices remain available in the viewer and are not pooled. V1 contains {v1['calls']} calls; v2 contains {v2['calls']} calls ({v2['valid_calls']} valid). This is development iteration, not a blinded holdout. An earlier sandbox-localhost setup failure made no provider calls; its traces are retained separately in `records/setup-network-failure` and excluded from both pilots. Browser integration calls are excluded too.

The traffic correction removed the immediate rear-end pattern in the direct destination comparison: both corrected runs travelled about 170m before leaving the map. It did not solve the routing failure. This is why validating the environment matters before attributing a failure to the model.

## Tokens per question — not a split of a request total

Each request contains exactly one question. Values below are provider-reported input/output usage for that question, including serialized state, question instructions and provider formatting counted by the API. They are not just the words visible in a short question. We cannot independently separate provider-internal overhead from the reported input count. The two questions repeat the state, which increases cost compared with a joint request; it permits exact question-level attribution.

| Question | Calls | Mean input tokens (range) | Mean output tokens (range) | Median API latency, ms |
|---|---:|---:|---:|---:|
{chr(10).join(usage)}

The [CSV](records/pilot-v2/per-question.csv) contains every individual question's actual counts, choice, latency and observation age. Raw responses are in each episode JSON. Decision latency also includes proxy/transport overhead and waits for both requests; it is not the sum of question latencies. No unavailable usage is estimated.

## Vision and assistance boundaries

The [official API reference](https://docs.typesafe.ai/api) describes `state` as text or structured data, and [State documentation](https://docs.typesafe.ai/concepts/state) explains its serialization. We did not verify a native image interface for this pinned model. The interface therefore labels native vision unavailable instead of passing encoded image bytes as text and claiming image understanding. Screenshot capture works and can support a future separately disclosed perception pipeline. These results test neither native image reasoning nor an external vision model.

## Validation and limitations

The shared engine runs in Node and the browser. Offline validation re-executes the raw recorded model choices and compares final physics and event lists exactly. Source hashes in each manifest are verified against the applicable snapshot. Nineteen automated tests cover deterministic seeds, collisions, red lights, stopping, action mapping, exact clock behavior, late replies, API failures, traffic following, four turn calibrations and an end-to-end destination trajectory without traffic. That calibration proves one trajectory is reachable; it does not certify that every benchmark situation or maneuver is easy or fair. Browser checks cover live requests, tokens, stop, manual controls, replay, seek, cameras, downloads, mobile layout and public mode. See [QA](QA.md).

Important limits: only one seed, one map, one prompt formulation per technique, no option-order randomization, no independent repetitions, sequential rather than randomized condition order, and no controlled latency sweep. Numerical telemetry is privileged simulator information. Flat bicycle dynamics, approximate 1.8m-radius circle collision envelopes (not conservative at every angle relative to the rendered car) and scripted traffic are much simpler than real driving. Only selected 90-degree turn trajectories are calibrated; the maneuver executor is not a certified planner. We do not separately penalize wrong-way driving or prove every unsafe behavior is detected. The model may fail because of state representation, insufficient decision frequency, action granularity, conflicting atomic choices, routing, or interactions; this pilot does not isolate those mechanisms.

## Next experiments, not claims

1. Separate route selection from motor execution with frozen same-state junction questions and measured lane/signal tasks. Keep route recommendations out of the unassisted condition.
2. Compare raw numerical state against prose and egocentric measurements on development seeds, freeze the winning prompt, then test new held-out traffic/layout seeds.
3. Inject controlled delays on identical recorded observations and compare 0.2/0.6/1.2-second decision periods. Distinguish latency effects from changed model answers.
4. Calibrate traffic and every maneuver with independent scripted controls, including emergency stops and U-turns; classify failure responsibility before interpreting a collision as model error.
5. Test vision only after validating a documented image interface. If another model performs perception, report its accuracy, latency and cost separately.

These are proposed experiments. No results from them are implied by this report.
'''
(ROOT / 'REPORT.md').write_text(report)
print('Wrote verified report for', v2['episodes'], 'v2 episodes')
