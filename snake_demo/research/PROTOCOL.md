# Classic Snake diagnosis: frozen initial protocol

This extends the original study; it does not replace its failed games. Model:
`jev-1.13.0`. Board: Classic 12×12, initial length 3, solid boundaries, eight-food
target, 200 moves, 50 moves without food. Fresh requests carry no conversation
history. Model/provider independence and absence of backend caching cannot be
established by a client. All calls and failures are retained, no retry.

## Objective and falsifiable hypotheses

The requested aspiration is perfect, efficient Snake. We operationalize and
report separately: legal actions, exact shortest-path actions to the CURRENT
food, eight-food task completion, and path efficiency per food segment.
Shortest-path means minimum number of legal turns with the body/tail moving;
Manhattan distance alone is not ground truth. No claim of globally minimum
moves across unknown future food or universal Snake victory follows.

- H1: shorter, task-specific state/instructions improve decisions over the
  original full-state prompt. Compare paired states, without computed hints.
- H2: absolute direction choice keys reduce relative-turn confusion. Compare
  the compact relative and absolute variants, preserving candidate destinations.
- H3: external safety/distance features help more than wording alone. The local
  variant explicitly supplies immediate legality and Manhattan distance; it is
  assisted and cannot establish independent model calculation.
- H4: supplying exact dynamic-body route lengths improves shortest-action
  selection. This gives away the planning solution; assess numeric selection
  compliance separately from planning ability.
- H5: choice ordering and repeated identical payloads can change decisions.
  Cross every permutation twice on fixed development states, keeping the state
  fixed. Compare returned choices and probability argmax, including ties.
- H6: narrow safety/one-step progress questions succeed more often than route
  selection. Each atomic question uses a SEPARATE call to preserve exact token
  attribution. Their outputs do not form an implicit chain of thought.
- H7: a code verifier rejecting non-shortest actions can deliver stronger system
  performance than the model alone. Count EVERY overridden proposal; attribute
  the constraint to the exact planner. Never call this unassisted Jev accuracy.

## Frozen experiment stages

1. Offline audit of previous Classic games: immediate safety, shortest-action
   agreement, choice/argmax agreement, and confidence on errors. Exact A* has a
   100,000-expanded-node budget per candidate; unresolved states are unknown.
2. Development corpus: 60 fixed states sampled evenly from old direct, old
   baseline, and fresh random-legal trajectories. Seeded selection before new
   calls. Five variants: original, compact, absolute, local, exact.
3. Holdout corpus: 60 states from new baseline/random trajectories (seeds
   301–320), selected before calls and disjoint from development board states.
   Evaluate all five frozen variants once; do not tune on holdout results.
4. Order/repetition audit: first 12 development states, original prompt, all six
   option permutations × two repetitions = 144 calls. Atomic safety and
   Manhattan-progress audit: first 30 development states × three actions × two
   questions = 180 single-question calls. Total fixed-state maximum: 924 calls.
5. Select the best unassisted variant (original/compact/absolute) by DEVELOPMENT
   shortest-action accuracy, then immediate-safety accuracy, then listed order.
   Select best assisted variant (local/exact) identically. Freeze this selection
   before inspecting held-out gameplay. Run both plus exact-proposal-and-shield
   and code-only exact planner on 16 new seeds 1001–1016. Four concurrent games,
   sequential turns within a game. At most 9,600 API requests. Identical seeds
   share initial food; subsequent food can diverge with body occupancy.
6. If shield completes all 16 games with every resolved move shortest, expand
   code-only planner to 100 new seeds 2001–2100 to stress the actual guarantee.
   This tests code, not 100 extra Jev games. Otherwise report the failure and
   diagnose it rather than silently selecting another seed set.

No free-form prompt tuning after holdout. Additional hypotheses or interventions
require a dated amendment with new development/test partitions before calls.
The study stops after the defined stages; failures cannot be erased by rerunning
until a perfect batch appears. If the target is unmet, report that clearly and
specify the remaining barrier; finite experiments cannot prove universal 100%.

## Metrics and evidence

Save each exact payload, response text, parsed response, model/version, HTTP
status when available, time, latency, question identifier, and exact provider
input/output tokens. Errors record type/status and unknown usage, without keys.
One question per request throughout. Save all game before/after states, model
proposal, executed move, intervention flag, oracle costs/path certificate, and
termination. Planner search time is separate from API latency.

Report counts/denominators and Wilson 95% intervals for descriptive accuracy;
fixed-state samples contain within-trajectory dependence, so intervals are not
population guarantees. Report paired improvement/disagreement counts, not
unadjusted significance claims across this exploratory family. Eight-food
success is distinct from filling the board. Perfect observed accuracy is still
finite-sample evidence. Keep test-set selection and code-assisted facts visible.
