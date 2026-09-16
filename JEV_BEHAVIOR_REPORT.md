# Jev 1.13.0 behavior study: wording, prerequisites, and long context

Prepared 2026-09-16. Synthetic test inputs; observed live API responses.

## Jev is sensitive to the decision frame, even when it recognizes the necessary facts

The strongest result is a mismatch between recognizing requirements and applying them to an action. Jev 1.13.0 repeatedly recognized that a car must be present to be washed, but often chose walking when a short walking distance was mentioned. Controlled interventions changed that behavior: omitting the distance, describing driving as bringing the car, or explicitly supplying the prerequisite facts often restored the correct choice.

The expanded investigation contains **2,805 new API requests across 251 configured conditions**, supplementing the five earlier 1,000-request runs. There were no API errors in either new study. The new requests produced 3,280 scored answers; some requests contained multiple questions. All returned model version `jev-1.13.0`.

On 12 balanced synthetic travel scenarios, direct action selection was correct in **65/120 requests (54.2%)**. Two prerequisite checks were jointly correct in **110/120 (91.7%)**. More descriptive choices reached **225/240 (93.8%)** on those reused scenarios and **148/160 (92.5%)** on eight additional scenarios. Those are useful improvements, not universal guarantees.

The report recommends explicit action meanings, narrow feasibility checks, and code that rejects inconsistent answers. It does not claim to identify the model's hidden reasoning process. These are synthetic, deliberately challenging examples; the percentages are not estimates of general intelligence or production accuracy.

## What the original tests actually established

The original carwash prompt was “I'm going to the carwash and it's really close, should I walk or should I drive? Answer only walk or drive.” The revised prompt was “I need to wash my car. The car wash is a 5-minute walk from my home. Should I walk or drive there?” Both supplied empty state and walk/drive choices.

The successful decomposed test supplied the context “I want to have my car washed at a car wash located a 5-minute walk from my home.” Question A asked whether the car must physically be present; question B asked whether walking there and leaving the car home would accomplish the goal. Both were sent together with yes/no/cannot_be_determined choices.

The original letter-count prompt preserved the user's spelling `straberry`. Both `straberry` and standard `strawberry` contain three r characters. The expected count is case-insensitive. Each original test repeated a single configuration 1,000 times. That establishes response stability for those configurations, not broad task coverage. Two earlier failed startup attempts, one DNS failure and one authentication failure, produced no model answers and are excluded from accuracy and reported-token totals.

| Earlier test | Correct | Accuracy | Input/request | Output/request |
| --- | --- | --- | --- | --- |
| Flat Earth: yes/no | 1,000/1,000 | 100% | 311 | 31 |
| Carwash: original wording | 5/1,000 | 0.5% | 327 | 31 |
| Car wash: explicit goal | 0/1,000 | 0% | 327 | 31 |
| R count: original “straberry” | 1/1,000 | 0.1% | 426 | 95 |
| Car wash: A and B together | 1,000/1,000 jointly | 100% | 441 | 81 |

## Study design, labels, and what “scaled text” means

The first study ran from 2026-09-16T07:56:59.569088+00:00 to the start of its last request at 2026-09-16T08:00:11.919441+00:00. Its exact cases, expected labels, schedule, and hypotheses were saved before calls began. The second study ran from 2026-09-16T08:04:33.684299+00:00 to 2026-09-16T08:05:38.347117+00:00 and was designed after inspecting the first study. It is an adaptive follow-up, not an independent preregistered confirmatory experiment.

Within each study, a fixed random seed shuffled requests from all conditions. Four workers used fresh HTTP openers, without cookies, conversation history, response reuse, or automatic retries. The authorization credential and hosted provider were shared. This isolates supplied inputs, not provider infrastructure or hidden server state. Batch submission was bounded to 40 scheduled requests; multiple questions were grouped only where the design called for them.

The model was pinned to `jev-1.13.0`. Each raw response, request-body hash, UTC start time, and latency is preserved. Scoring uses the selected `choice`, never a probability threshold. A multi-question request passes the strict joint metric only when every selected answer matches its predeclared label. Expected labels are local scoring metadata and are not included in model inputs.

Travel examples have six drive-required and six walk-required scenarios in the main transfer panel. New follow-up examples have four of each. They explicitly constrain vehicle location, availability, or the need for a vehicle, so walking is not always marked wrong. Exact-count labels were computed with Python's case-insensitive string counting. Travel labels are analyst-authored and have no external adjudication.

Scaled text means 0, 256, 1,024, 4,096, or 8,192 added whitespace-delimited filler words, with the relevant scenario at the beginning, middle, or end. One filler repeatedly describes ordinary neighborhood records; another describes an unrelated resident walking to a bakery. The largest request reported 11,496 input tokens. Repeated filler is a controlled stress test, not a substitute for diverse natural long documents.

| Experiment | Conditions | Requests | Allocation |
| --- | --- | --- | --- |
| Factorial wording/context/options | 16 | 400 | 25 per condition |
| Questions alone versus together | 5 | 125 | 25 per condition |
| Question-ID control | 2 | 50 | 25 per condition |
| Detailed choices / generic rule | 2 | 50 | 25 per condition |
| Balanced scenario transfer | 36 | 360 | 12 scenarios × 3 methods × 10 |
| Length, position, and filler | 50 | 400 | 8 per condition |
| Balanced transfer with long text | 32 | 160 | 5 per condition |
| Counting strings and formats | 48 | 480 | 16 strings × 3 formats × 10 |
| Follow-up: descriptive choices | 40 | 400 | 20 scenarios × 2 option orders × 10 |
| Follow-up: distance cues | 5 | 100 | 20 per condition |
| Follow-up: placement replication | 4 | 100 | 25 per condition |
| Follow-up: counting wording | 8 | 120 | 15 per condition |
| Follow-up: supplied prerequisites | 3 | 60 | 20 per condition |

## Distance wording can dominate an unchanged car-washing goal

This follow-up held “I need to wash my car,” the question “Should I walk or drive there?”, the walk/drive choices, and state placement fixed. Only the distance sentence changed. “Absent” means no distance information; walk5 and drive5 mean a five-minute walk or drive; meters100 means 100 meters; km50 means 50 kilometers.

Removing distance restored 20/20 correct drive choices. Describing the distance as a five-minute walk produced 0/20 correct choices; a five-minute drive produced 20/20. A 100-meter distance produced just 2/20 drive choices, whereas 50 kilometers produced 20/20. Because the car must be brought regardless of proximity, the distance cue should not reverse the answer under the intended scenario.

The no-distance condition also removes the explicit destination sentence, leaving “I need to wash my car” and “Should I walk or drive there?” Its destination is therefore underspecified; it is not a perfectly isolated distance-removal comparison. The five-minute-walk versus five-minute-drive pair is the cleaner contrast: the destination and numerical duration remain fixed while one transportation word changes.

This supports sensitivity to proximity and transportation wording. It weakens the explanation that Jev simply lacks the fact that cars must be present. It does not prove an internal nearest-neighbor shortcut, attention failure, or a particular training-data association. The interventions alter meaningful linguistic content; no internal activations or training records were observed. This panel has one underlying scenario, with 20 repetitions per condition.

| Distance condition | Correct drive | Accuracy | Input/request | Output/request |
| --- | --- | --- | --- | --- |
| absent | 20/20 | 100.0% | 315.0 | 31.0 |
| walk5 | 0/20 | 0.0% | 327.0 | 31.0 |
| drive5 | 20/20 | 100.0% | 327.0 | 31.0 |
| meters100 | 2/20 | 10.0% | 327.0 | 31.0 |
| km50 | 20/20 | 100.0% | 326.0 | 31.0 |

## Context placement interacts with the question, rather than helping uniformly

The 2×2×2×2 factorial varied: scenario inline in instructions versus in state; direct wording versus goal-focused wording; two choices versus adding cannot_be_determined; and normal versus reversed choice order. Each of the 16 cells had 25 repetitions. The table averages over the two option factors with equal weight.

The goal-focused instruction was “Which option accomplishes my goal of getting my car washed at the car wash?” With the scenario next to that question in instructions, it yielded 89/100 correct choices across option configurations. With the scenario in state, the same goal-focused question yielded 0/100. Direct wording yielded 0/100 in either location.

The follow-up replicated the two-choice, normal-order cells. Inline goal wording achieved 14/25, compared with 20/25 in the first study's exact matched cell. The other three cells stayed at 0/25. The direction of the placement interaction persisted, but the success level was unstable; do not advertise an 89% general success rate for this prompt.

This corrects the earlier recommendation that moving facts into state would necessarily improve behavior. State is the documented interface for facts, but correct schema use is not sufficient for accuracy. The study has no evidence that inline placement is universally superior either. Placement, wording, and the particular task must be validated together. The compared factorial cells had identical token counts when only placement changed.

| Scenario location | Question wording | Correct | Accuracy |
| --- | --- | --- | --- |
| inline | direct | 0/100 | 0.0% |
| inline | goal | 89/100 | 89.0% |
| state | direct | 0/100 | 0.0% |
| state | goal | 0/100 | 0.0% |

## Concrete action descriptions help more than a generic instruction to be careful

For the original revised scenario, bare choices were “Walk” and “Drive.” Defining walk as “Travel there on foot, leaving my car at home” and drive as “Travel there in my car, bringing it with me” produced 25/25 correct drive choices. This intervention exposes the consequences that the short labels leave implicit.

By contrast, adding “Choose the option that satisfies the goal and its necessary conditions. Consider convenience only among options that can accomplish the goal” before the direct question produced 0/25 correct choices. Mean confidence in this entirely wrong condition was 0.9744. A general reasoning instruction did not reliably activate the relevant constraint.

Across the full factorial, adding cannot_be_determined changed accuracy from 43/200 to 46/200. Reversing option order changed 41/200 to 48/200. Most of these cells failed regardless; these small marginal differences do not establish a broad remedy. The follow-up revealed a larger order effect on one new example, so option order should still be tested.

The question-ID control changed only `answer` versus `transport`. Both configurations selected walk in 25/25 requests, and both reported 327 input and 31 output tokens. This agrees with the API documentation that these IDs are not used in inference. It does not explain the other person's previously reported 344 input tokens; their complete request remains unavailable.

## Correct checks do not automatically correct another answer in the same request

A alone passed 25/25; B alone passed 25/25; A and B together both passed 25/25. Asking both at once was therefore not necessary for their success.

More decisively, when A, B, and the direct transportation question were placed in the same request, every response answered A=yes, B=no, and transport=walk. All 25 combined responses contained that practical inconsistency. Merely adding helpful questions to a batch did not make their conclusions feed into the final choice.

A separate follow-up supplied the prerequisite conclusions explicitly as input state. Writing the facts in ordinary sentences restored 20/20 correct drive choices. Stating them as previously checked yes/no results also restored 20/20. The unchanged baseline remained 0/20. These were fixed, truthful facts consistent with earlier responses, not fresh upstream model calls in an end-to-end pipeline.

The observed distinction is between asking related questions alongside an action question and actually supplying the necessary information to that action question. TypeSafe documents independent evaluation of questions. An application should combine their results in code or explicitly pass validated results into another request; it should not assume question order creates an internal reasoning chain.

| Questions in request | Selected-answer counts | Input/request | Output/request |
| --- | --- | --- | --- |
| A | {"A": {"yes": 25}} | 356 | 42 |
| B | {"B": {"no": 25}} | 365 | 42 |
| A-B | {"A": {"yes": 25}, "B": {"no": 25}} | 441 | 81 |
| transport | {"transport": {"walk": 25}} | 328 | 31 |
| A-B-transport | {"A": {"yes": 25}, "B": {"no": 25}, "transport": {"walk": 25}} | 489 | 109 |

## Prerequisite checks transfer better, but fail on a trade-in inspection

The 12-scenario panel includes washing, tire replacement, inspection, oil change, vehicle weighing, and trade-in inspection as drive-required tasks. Walk-required tasks include collecting an already-present car, attending a job interview with no vehicle available, collecting a receipt with the road closed, buying a sponge with an undriveable car, discussing a refund without a vehicle, and delivering paperwork while a mobile service washes the car at home.

Each scenario was tested ten times with direct selection, goal-focused selection, and two generic checks. The checks ask whether bringing a car from home is required and whether walking without one accomplishes the stated goal. Jointly correct checks improved by 37.5 percentage points over direct selection on this balanced panel. These are different output tasks: the checks' 91.7% is not a directly observed 91.7% drive/walk selection rate.

The failure is specific and informative: for physical trade-in inspection, the model said the car need not be brought, but also said walking without it would not accomplish the goal. That no/no pair occurred in all ten repeats. Eleven of twelve scenarios had perfect joint checks; this one failed consistently.

A post-hoc code rule could issue drive only for yes/no and walk only for no/yes, abstaining otherwise. Applied offline to these recorded checks, it would cover 110/120 requests, all correctly, and abstain on the ten trade-in cases. That is selective performance on the development panel—not a validated production guarantee or a live test of a complete action system.

| Method | Correct requests | Accuracy | Drive-required | Walk-required |
| --- | --- | --- | --- | --- |
| direct | 65/120 | 54.2% | 5/60 | 60/60 |
| goal | 61/120 | 50.8% | 1/60 | 60/60 |
| checks | 110/120 | 91.7% | 50/60 | 60/60 |

## Descriptive choices generalize imperfectly to additional scenarios

After the promising 25/25 result, the follow-up used two explicitly described actions across 20 scenarios and both option orders, ten repetitions per condition. The walk description was “Travel there on foot, leaving any car at home where it is”; the drive description was “Travel there in my car, bringing it with me.” This slightly generalized description differs from the first single-case probe and is recorded verbatim in the manifest.

On the 12 reused scenarios, this configuration reached 225/240 correct choices (93.8%), versus 65/120 for bare direct choices in the first study. Because the rounds and option-order mix differ, this is not a simultaneous, perfectly matched estimate of a single treatment effect. On eight newly authored scenarios it reached 148/160 (92.5%). Those new cases cover brakes, alignment, windshield replacement, body-shop painting, collecting keys, a tire-shop interview, collecting a manual, and delivering a form.

All follow-up errors were concentrated in two scenarios. Trade-in inspection succeeded in 4/10 trials with normal order and 1/10 with reversed order. Collecting spare keys when the only car was already at the locksmith succeeded in 8/10 with normal order and 0/10 with reversed order. Eighteen of the twenty scenarios were perfect across both orders, but those two are material failures.

The new examples were authored after seeing the initial results; “new” means not in the first study, not a blinded or independently sampled holdout. No bare-choice baseline was run for those eight new cases, and descriptive choices were not stress-tested at 8,192 words. These limits prevent claiming a universally best strategy.

| Scenario cohort | Distinct scenarios | Correct choices | Accuracy |
| --- | --- | --- | --- |
| reused | 12 | 225/240 | 93.8% |
| new | 8 | 148/160 | 92.5% |

## Explicit checks usually survived the long filler tests; direct choices failed even without filler

Across all 200 direct-choice long-context requests, Jev chose the wrong action. It was already wrong with zero filler, so this panel cannot establish that extra text caused the direct-choice failure. The task was at an accuracy floor.

Both checks were correct in 196/200 requests. Four failures occurred at 4,096 neutral filler words: three of eight with the task in the middle and one of eight with the task at the end. In each failure, the car was recognized as required, but walking without it was also judged to satisfy the goal. At 8,192 words, both checks were correct in all 48 requests. The pattern is not a monotonic context-length collapse and does not identify a reliable length threshold.

The walking-related filler did not produce a demonstrated accuracy decrease relative to neutral filler in this panel. It would be incorrect to claim that the test proved “walking priming” from distractors. Successful checks may also benefit from general knowledge and strongly revealing question wording, so these results do not prove perfect retrieval of long documents.

A second long-text panel included four scenarios, two drive-required and two walk-required, at 512 and 4,096 neutral filler words with facts at the start or end. Direct selection was 40/80: every walk case passed and every drive case failed. Both checks passed in all 80 requests. That reduces the concern that the long-text success was simply a fixed yes/no answer pattern, but still covers only four scenarios.

| Added filler words | Direct correct | Both checks correct | Check accuracy | Mean input/request, checks |
| --- | --- | --- | --- | --- |
| 0 | 0/8 | 8/8 | 100.0% | 437.0 |
| 256 | 0/48 | 48/48 | 100.0% | 760.2 |
| 1,024 | 0/48 | 48/48 | 100.0% | 1,728.0 |
| 4,096 | 0/48 | 44/48 | 91.7% | 5,606.2 |
| 8,192 | 0/48 | 48/48 | 100.0% | 10,774.2 |

## Counting is wording-sensitive and remains unsuitable for exact computation

The main counting panel used 16 strings: straberry, strawberry, strawberries, raspberry, blueberry, cherry, banana, river, error, rrr, r, rrrrrr, abracadabra, qrzrpr, rrabr, and RrR. Each was tested ten times in plain form, with spaces inserted between characters, and with an instruction to examine every character and count each r or R once. All used numeric choices 0–10 and an explicitly case-insensitive question.

Plain text was correct in 92/160 requests, spaced characters in 100/160, and the explicit counting instruction in 88/160. Spacing improved some cases but broke others: it fixed strawberry and raspberry in this panel, but failed on abracadabra and rrabr. Both plain and spaced variants failed on blueberry and error. Instructions to count carefully did not establish a reliable algorithm.

The follow-up disentangled the original phrase “How many R's” from “How many occurrences of the letter r, ignoring case.” For straberry, original wording yielded 0/15 correct trials both inline and in state; explicit wording succeeded in 14/15 inline and 15/15 in state. For standard strawberry, all four configurations failed in every trial. The earlier near-zero straberry result therefore does not describe every wording, and improvement on that spelling did not transfer even to strawberry.

This supports representation and phrasing sensitivity. It does not reveal whether tokenization, memorized associations, upper/lowercase interpretation, or another internal mechanism caused the errors. The explicit wording intervention changes several linguistic features, so attributing the improvement solely to lowercase r would be unwarranted. Use deterministic string processing for exact counts.

| Counting input/method | Correct | Accuracy | Mean input/request | Output/request |
| --- | --- | --- | --- | --- |
| plain | 92/160 | 57.5% | 429.6 | 95 |
| spaced | 100/160 | 62.5% | 433.6 | 95 |
| algorithm | 88/160 | 55.0% | 443.6 | 95 |

## Selected answers, probabilities, confidence, and accuracy are different measurements

The selected choice is the actual answer used for pass/fail. The probability assigned to a correct option is not how often that option was selected across repeated requests. In the original revised car wash test, drive received an average score of 0.11283 while the actual drive-selection rate was zero. The API documents the choice as the highest-probability option, rather than a sample drawn from its reported distribution.

Confidence summarizes the concentration of option scores. It is not an independent correctness check or a promised pass rate. In the first new study, the 0.80–0.95 confidence bin had lower observed accuracy than either lower bin. Even the highest bin contained errors. The generic feasibility-rule prompt averaged 0.9744 confidence while being wrong in all 25 trials.

The table below is a descriptive diagnostic over the first study's 2,500 individual answers. It mixes question types, repeated examples, and deliberately difficult conditions. It is not a production calibration study, does not compare equal task mixtures across bins, and must not be used to choose a universal confidence threshold. No probability calibration curve, claim of global miscalibration, or p-value is inferred from this selected panel.

Repeated failures do not become reliable merely because majority voting agrees. Repetition mostly measures stability conditional on a fixed prompt. A deployment needs labeled, representative tasks, separate threshold tuning and evaluation sets, and explicit checks for contradictory outputs.

| Returned confidence range | Individual answers | Observed accuracy |
| --- | --- | --- |
| 0.00–0.50 | 434 | 49.8% |
| 0.50–0.80 | 530 | 50.9% |
| 0.80–0.95 | 649 | 42.1% |
| 0.95–1.00 | 887 | 83.1% |

## Token usage is reported per API request, including all questions in that request

The provider reports input and output usage but does not expose a token-by-token breakdown of its internal prompt formatting. These are not counts of the user's visible sentence alone. Every result retains the raw usage fields; summaries below show per-request values, not total-run values, except where explicitly labeled.

Asking A and B separately used 356+365=721 input tokens and 42+42=84 output tokens across two requests. Combining them used 441 input and 81 output tokens: 280 fewer input tokens, a 38.8% reduction for that pair, and one fewer round trip. This is a measured request-usage comparison, not a billing claim. The API does not assign separate token usage to each question within a batch.

The first study used 2,922,028 input and 119,445 output tokens; the follow-up used 282,340 input and 31,860 output tokens. New-study totals are 3,204,368 input and 151,305 output. Including the five historical completed runs gives 5,036,368 reported input and 420,305 reported output tokens over 7,805 successful requests. Failed startup attempts had no reported usage; they are not assumed to have zero billed cost.

Long context increased input usage substantially while the typed output shape stayed fixed. The 11-choice count questions used 95 output tokens; binary travel choices used 31; paired three-way checks used 81. These measurements do not establish that all future requests of the same visible length will have the same usage.

| Configuration | Input/request | Output/request | Scope |
| --- | --- | --- | --- |
| Revised direct car wash | 327 | 31 | 1 choice |
| A alone | 356 | 42 | 1 three-way choice |
| B alone | 365 | 42 | 1 three-way choice |
| A and B together | 441 | 81 | 2 three-way choices |
| A, B and transport together | 489 | 109 | 3 choices |
| Original described-action probe | 347 | 31 | 1 choice |
| Direct with supplied prerequisite facts | 356 | 31 | 1 choice |
| Direct with previous-check facts | 357 | 31 | 1 choice |
| Original straberry count | 426 | 95 | 11 numeric options |
| 8,192-word carwash context, checks | 10,774.2 mean | 81 | 2 choices; varies by filler and position |

## Hypotheses: what the evidence supports and what remains unresolved

“Supported” means the observed intervention produced the predicted pattern within the tested conditions. It does not mean a universal law or a proven account of internal model computation. The follow-up was chosen adaptively, and multiple comparisons were explored. No significance claims are made. Exact prompts and individual results are available for replication.

| Hypothesis | Assessment | Evidence / limit |
| --- | --- | --- |
| Short-distance language can override the goal | Supported in the carwash panel | 0/20 with five-minute walk; 20/20 with no distance or five-minute drive. Internal mechanism unresolved. |
| Moving facts to state always improves results | Rejected as a general rule | Inline goal wording outperformed split state on this item; neither location fixed direct wording. |
| Explicit action consequences help | Supported with exceptions | 225/240 on reused scenarios, 148/160 on new scenarios; locksmith and trade-in failures remain. |
| Adding a generic reason-carefully rule is enough | Not supported | 0/25 with a generic feasibility-first instruction. |
| Batching prerequisite questions creates a reasoning chain | Not supported | A and B correct but transport wrong in all 25 three-question requests. |
| Supplying prerequisite conclusions can fix selection | Supported on one scenario | 20/20 with natural-language facts and 20/20 with previous-check facts. Not a live chained evaluation. |
| Explicit checks generalize to balanced tasks | Partially supported | 110/120 jointly correct across 12 scenarios; trade-in consistently failed. |
| Longer text steadily worsens accuracy | Not supported by this experiment | Four check errors at 4,096 words, none at 8,192; direct-choice floor prevents causal attribution. |
| Walking-themed filler causes more failures | Not demonstrated | All four long-check errors occurred with neutral filler. |
| Option order never matters | Rejected on a new case | Locksmith collection: 8/10 correct normal order, 0/10 reversed. Small case-specific sample. |
| The question key explains behavior/token changes | No observed support | answer and transport controls both 0/25 and both 327/31 tokens. |
| Spacing or counting instructions make exact counting reliable | Rejected on this panel | Best aggregate method was 62.5%; multiple strings failed consistently. |
| High confidence is a correctness guarantee | Rejected | 0/25 correct at mean confidence 0.9744 in a rule prompt. |

## Recommended interaction method, with explicit limits

Start from the real decision and its prerequisites. Put factual records and constraints in clearly named context fields where practical, but treat this as an interface convention to validate, not an accuracy guarantee. Keep the goal explicit in the decision instruction. Describe each action's concrete consequences instead of relying entirely on short labels such as walk and drive.

For decisions that depend on hidden prerequisites, ask narrow checks: whether an object must be present, whether each candidate action accomplishes the goal, and whether the action is feasible under the supplied constraints. Ask only independent checks together. Combining their outputs is the application's responsibility. A separate drive-feasibility question is a proposed improvement and was not evaluated in this study.

In the tested travel setting, interpret the two checks conservatively: bring=yes and walking-succeeds=no permits considering drive; bring=no and walking-succeeds=yes permits considering walk; inconsistent or unknown pairs should trigger review or a better model. Validate real feasibility before taking action. The post-hoc development-panel result for this policy was 91.7% coverage with no errors among issued recommendations, not a general guarantee.

If you use a second request for synthesis, explicitly include the checked prerequisites in its input. Do not merely place a final recommendation question alongside earlier questions and assume it reads their answers. The fixed-fact follow-up supports this approach on one example; a complete live two-stage system, including propagation of mistaken first-stage checks, still needs evaluation.

Use cannot_be_determined when evidence can be insufficient, but do not treat an uncertainty option as an accuracy fix. Evaluate option order and label descriptions. Route conflicts and out-of-scope cases explicitly; choose probability thresholds from held-out task data, not from a convenient number or these challenge-set bins.

Keep deterministic operations in code: character counts, arithmetic, schema checks, fixed rules, and known business constraints. For research, pin the version, preserve request JSON, log selected choices separately from probabilities, and record usage per request. For deployment, measure accuracy across distinct cases, coverage under abstention, contradictions, and token/latency costs. Thousands of repeats of one easy or hard item cannot replace that evaluation.

## Limits, alternative explanations, and corrections to earlier claims

The experiments are single-provider, single-version, short-window measurements on synthetic tasks authored in this conversation. No competing model was tested. The new study contains 251 configurations, but many share the same underlying case; they are not 251 independent reasoning domains. There are 20 distinct travel scenarios across the two rounds and 16 exact-count strings, with substantial reuse.

Provider-side caching, routing, hidden preprocessing, sampling settings, and model internals were not controlled. Fresh HTTP requests prevent client-side history reuse but cannot prove statistical independence. No temperature or seed controls were sent to Jev. The shuffled order reduces simple temporal confounding within each round, not across the separately designed rounds.

The long-text filler repeats two short templates, and some questions strongly disclose the needed relationship. Results do not establish comprehensive long-document comprehension, immunity to prompt injection, or robustness to conflicting evidence. No adversarial instructions were included. Distance effects were isolated on one carwash scenario; new-scenario baselines and long-context descriptive-choice tests remain missing.

Travel labels are based on the supplied constraints and ordinary interpretation. They are not externally adjudicated. The broad direct question can invite convenience-based advice, whereas the intended metric requires accomplishing the service goal. That mismatch is part of the behavior being measured; the report does not claim the model literally lacks all relevant knowledge.

Corrections to earlier discussion: the average drive score was not a pass rate; 100% repeated selections were not 100% probability. Both spellings straberry and strawberry have three r characters. Separating state and instructions was a recommendation from documentation, not an established empirical fix, and this study found a counterexample. Question IDs do not explain the previously observed 17-token discrepancy. Finally, the two-question 100% result showed success on prerequisites, not a tested final walk/drive recommendation.

The report deliberately avoids treating these repeated requests as independent population samples, attaching misleading confidence intervals, or claiming a causal internal mechanism from output traces. Differences between conditions are observed behavioral effects; generalization remains bounded by the examples tested.

## Further tests that would resolve remaining uncertainty

The highest-value next evaluation is a separately authored, blinded set of tasks where the correct action depends on different prerequisites, with balanced labels and realistic language. Freeze the prompt strategy before collecting that set. Compare bare choices, descriptive choices, explicit checks with abstention, and a genuine two-stage pipeline on the exact same scenarios and request budget.

For the distance hypothesis, cross walking-versus-driving wording with numerical proximity over many goals, including goals that really do favor walking. For context placement, cross the same semantic content and question with structured state, flat state, inline instructions, and explicit field references, preserving wording and option descriptions wherever possible.

For long context, replace repetitive filler with varied, labeled natural documents; measure retrieval of case-specific facts, conflicting facts, entity mix-ups, and beginning/middle/end placement. Include no-answer cases. Test the descriptive-choice method under length scaling instead of assuming its short-context success transfers.

For uncertainty, evaluate held-out accuracy and abstention coverage by task family and option count. A deployment-ready claim requires performance across new cases and sustained runs, not another thousand repeats of the original carwash puzzle. No additional requests beyond the documented two rounds were made for these proposed tests.

## Evidence, documentation, and reproducibility

The main empirical sources are the five historical runs and the two new study directories `20260916T075659560245Z-behavior-study` and `20260916T080433683304Z-behavior-followup`. Each new directory contains manifest.json, schedule.json, raw results.jsonl, completion.json, analysis.json, conditions.csv, and answers.csv. The manifest contains every exact request payload and expected label. Hashes bind each raw response record to its request. The schedules preserve the randomized order.

Run `python analyze_behavior_study.py results/20260916T075659560245Z-behavior-study` and the corresponding command for `20260916T080433683304Z-behavior-followup` to revalidate and regenerate the condition and answer tables without sending API requests. Run `python build_behavior_report.py` to regenerate this report . The API runners are `behavior_study.py` and `behavior_followup.py`; rerunning those incurs new API usage. No credentials are included in report data or evidence files.

TypeSafe documentation was read during this investigation and the preceding analysis. It describes Jev as a structured decision model, distinguishes state from questions, describes independent question evaluation, and states that choice returns the highest-probability option. These are provider descriptions, not independent proof of internal implementation:

- [System One](https://docs.typesafe.ai/concepts/system-one)
- [State and independent questions](https://docs.typesafe.ai/concepts/state)
- [API fields and choice semantics](https://docs.typesafe.ai/api)
- [Confidence](https://docs.typesafe.ai/confidence)
- [Recommended workflow](https://docs.typesafe.ai/concepts/how-to-build-with-system-one)

Validation independently parsed every raw response, recomputed every selected-answer outcome, checked schedule membership and unique trial IDs, verified payload hashes and returned model versions, and reconciled token totals. Displayed probabilities are rounded, so their sums were checked with an explicit rounding tolerance rather than requiring exact floating-point equality. The reproducibility appendix lists all configured conditions, including failures.

## Appendix: every new condition

Token values are means per request. Multi-question accuracy requires every answer to be correct.

| Condition | Correct/requests | Accuracy | Input/request | Output/request |
| --- | --- | --- | --- | --- |
| factor-inline-direct-0-0 | 0/25 | 0.0% | 327.0 | 31.0 |
| factor-inline-direct-0-1 | 0/25 | 0.0% | 327.0 | 31.0 |
| factor-inline-direct-1-0 | 0/25 | 0.0% | 345.0 | 42.0 |
| factor-inline-direct-1-1 | 0/25 | 0.0% | 345.0 | 42.0 |
| factor-inline-goal-0-0 | 20/25 | 80.0% | 338.0 | 31.0 |
| factor-inline-goal-0-1 | 23/25 | 92.0% | 338.0 | 31.0 |
| factor-inline-goal-1-0 | 21/25 | 84.0% | 356.0 | 42.0 |
| factor-inline-goal-1-1 | 25/25 | 100.0% | 356.0 | 42.0 |
| factor-state-direct-0-0 | 0/25 | 0.0% | 327.0 | 31.0 |
| factor-state-direct-0-1 | 0/25 | 0.0% | 327.0 | 31.0 |
| factor-state-direct-1-0 | 0/25 | 0.0% | 345.0 | 42.0 |
| factor-state-direct-1-1 | 0/25 | 0.0% | 345.0 | 42.0 |
| factor-state-goal-0-0 | 0/25 | 0.0% | 338.0 | 31.0 |
| factor-state-goal-0-1 | 0/25 | 0.0% | 338.0 | 31.0 |
| factor-state-goal-1-0 | 0/25 | 0.0% | 356.0 | 42.0 |
| factor-state-goal-1-1 | 0/25 | 0.0% | 356.0 | 42.0 |
| batch-A | 25/25 | 100.0% | 356.0 | 42.0 |
| batch-B | 25/25 | 100.0% | 365.0 | 42.0 |
| batch-A-B | 25/25 | 100.0% | 441.0 | 81.0 |
| batch-transport | 0/25 | 0.0% | 328.0 | 31.0 |
| batch-A-B-transport | 0/25 | 0.0% | 489.0 | 109.0 |
| key-answer | 0/25 | 0.0% | 327.0 | 31.0 |
| key-transport | 0/25 | 0.0% | 327.0 | 31.0 |
| options-described | 25/25 | 100.0% | 347.0 | 31.0 |
| rule-feasibility | 0/25 | 0.0% | 350.0 | 31.0 |
| transfer-wash-direct | 0/10 | 0.0% | 333.0 | 31.0 |
| transfer-wash-goal | 0/10 | 0.0% | 344.0 | 31.0 |
| transfer-wash-checks | 10/10 | 100.0% | 439.0 | 81.0 |
| transfer-tires-direct | 0/10 | 0.0% | 335.0 | 31.0 |
| transfer-tires-goal | 0/10 | 0.0% | 346.0 | 31.0 |
| transfer-tires-checks | 10/10 | 100.0% | 441.0 | 81.0 |
| transfer-inspection-direct | 0/10 | 0.0% | 335.0 | 31.0 |
| transfer-inspection-goal | 0/10 | 0.0% | 346.0 | 31.0 |
| transfer-inspection-checks | 10/10 | 100.0% | 441.0 | 81.0 |
| transfer-oil-direct | 5/10 | 50.0% | 335.0 | 31.0 |
| transfer-oil-goal | 0/10 | 0.0% | 346.0 | 31.0 |
| transfer-oil-checks | 10/10 | 100.0% | 441.0 | 81.0 |
| transfer-weigh-direct | 0/10 | 0.0% | 336.0 | 31.0 |
| transfer-weigh-goal | 1/10 | 10.0% | 347.0 | 31.0 |
| transfer-weigh-checks | 10/10 | 100.0% | 442.0 | 81.0 |
| transfer-trade-direct | 0/10 | 0.0% | 337.0 | 31.0 |
| transfer-trade-goal | 0/10 | 0.0% | 348.0 | 31.0 |
| transfer-trade-checks | 0/10 | 0.0% | 443.0 | 81.0 |
| transfer-pickup-direct | 10/10 | 100.0% | 340.0 | 31.0 |
| transfer-pickup-goal | 10/10 | 100.0% | 351.0 | 31.0 |
| transfer-pickup-checks | 10/10 | 100.0% | 446.0 | 81.0 |
| transfer-job-direct | 10/10 | 100.0% | 335.0 | 31.0 |
| transfer-job-goal | 10/10 | 100.0% | 346.0 | 31.0 |
| transfer-job-checks | 10/10 | 100.0% | 441.0 | 81.0 |
| transfer-receipt-direct | 10/10 | 100.0% | 348.0 | 31.0 |
| transfer-receipt-goal | 10/10 | 100.0% | 359.0 | 31.0 |
| transfer-receipt-checks | 10/10 | 100.0% | 454.0 | 81.0 |
| transfer-supplies-direct | 10/10 | 100.0% | 339.0 | 31.0 |
| transfer-supplies-goal | 10/10 | 100.0% | 350.0 | 31.0 |
| transfer-supplies-checks | 10/10 | 100.0% | 445.0 | 81.0 |
| transfer-refund-direct | 10/10 | 100.0% | 340.0 | 31.0 |
| transfer-refund-goal | 10/10 | 100.0% | 351.0 | 31.0 |
| transfer-refund-checks | 10/10 | 100.0% | 446.0 | 81.0 |
| transfer-mobile-direct | 10/10 | 100.0% | 348.0 | 31.0 |
| transfer-mobile-goal | 10/10 | 100.0% | 359.0 | 31.0 |
| transfer-mobile-checks | 10/10 | 100.0% | 454.0 | 81.0 |
| length-0-neutral-start-direct | 0/8 | 0.0% | 331.0 | 31.0 |
| length-0-neutral-start-checks | 8/8 | 100.0% | 437.0 | 81.0 |
| length-256-neutral-start-direct | 0/8 | 0.0% | 677.0 | 31.0 |
| length-256-neutral-start-checks | 8/8 | 100.0% | 783.0 | 81.0 |
| length-256-neutral-middle-direct | 0/8 | 0.0% | 677.0 | 31.0 |
| length-256-neutral-middle-checks | 8/8 | 100.0% | 783.0 | 81.0 |
| length-256-neutral-end-direct | 0/8 | 0.0% | 676.0 | 31.0 |
| length-256-neutral-end-checks | 8/8 | 100.0% | 782.0 | 81.0 |
| length-256-walking-start-direct | 0/8 | 0.0% | 631.0 | 31.0 |
| length-256-walking-start-checks | 8/8 | 100.0% | 737.0 | 81.0 |
| length-256-walking-middle-direct | 0/8 | 0.0% | 633.0 | 31.0 |
| length-256-walking-middle-checks | 8/8 | 100.0% | 739.0 | 81.0 |
| length-256-walking-end-direct | 0/8 | 0.0% | 631.0 | 31.0 |
| length-256-walking-end-checks | 8/8 | 100.0% | 737.0 | 81.0 |
| length-1024-neutral-start-direct | 0/8 | 0.0% | 1712.0 | 31.0 |
| length-1024-neutral-start-checks | 8/8 | 100.0% | 1818.0 | 81.0 |
| length-1024-neutral-middle-direct | 0/8 | 0.0% | 1711.0 | 31.0 |
| length-1024-neutral-middle-checks | 8/8 | 100.0% | 1817.0 | 81.0 |
| length-1024-neutral-end-direct | 0/8 | 0.0% | 1712.0 | 31.0 |
| length-1024-neutral-end-checks | 8/8 | 100.0% | 1818.0 | 81.0 |
| length-1024-walking-start-direct | 0/8 | 0.0% | 1532.0 | 31.0 |
| length-1024-walking-start-checks | 8/8 | 100.0% | 1638.0 | 81.0 |
| length-1024-walking-middle-direct | 0/8 | 0.0% | 1533.0 | 31.0 |
| length-1024-walking-middle-checks | 8/8 | 100.0% | 1639.0 | 81.0 |
| length-1024-walking-end-direct | 0/8 | 0.0% | 1532.0 | 31.0 |
| length-1024-walking-end-checks | 8/8 | 100.0% | 1638.0 | 81.0 |
| length-4096-neutral-start-direct | 0/8 | 0.0% | 5861.0 | 31.0 |
| length-4096-neutral-start-checks | 8/8 | 100.0% | 5967.0 | 81.0 |
| length-4096-neutral-middle-direct | 0/8 | 0.0% | 5861.0 | 31.0 |
| length-4096-neutral-middle-checks | 5/8 | 62.5% | 5967.0 | 81.0 |
| length-4096-neutral-end-direct | 0/8 | 0.0% | 5860.0 | 31.0 |
| length-4096-neutral-end-checks | 7/8 | 87.5% | 5966.0 | 81.0 |
| length-4096-walking-start-direct | 0/8 | 0.0% | 5139.0 | 31.0 |
| length-4096-walking-start-checks | 8/8 | 100.0% | 5245.0 | 81.0 |
| length-4096-walking-middle-direct | 0/8 | 0.0% | 5141.0 | 31.0 |
| length-4096-walking-middle-checks | 8/8 | 100.0% | 5247.0 | 81.0 |
| length-4096-walking-end-direct | 0/8 | 0.0% | 5139.0 | 31.0 |
| length-4096-walking-end-checks | 8/8 | 100.0% | 5245.0 | 81.0 |
| length-8192-neutral-start-direct | 0/8 | 0.0% | 11390.0 | 31.0 |
| length-8192-neutral-start-checks | 8/8 | 100.0% | 11496.0 | 81.0 |
| length-8192-neutral-middle-direct | 0/8 | 0.0% | 11389.0 | 31.0 |
| length-8192-neutral-middle-checks | 8/8 | 100.0% | 11495.0 | 81.0 |
| length-8192-neutral-end-direct | 0/8 | 0.0% | 11389.0 | 31.0 |
| length-8192-neutral-end-checks | 8/8 | 100.0% | 11495.0 | 81.0 |
| length-8192-walking-start-direct | 0/8 | 0.0% | 9947.0 | 31.0 |
| length-8192-walking-start-checks | 8/8 | 100.0% | 10053.0 | 81.0 |
| length-8192-walking-middle-direct | 0/8 | 0.0% | 9947.0 | 31.0 |
| length-8192-walking-middle-checks | 8/8 | 100.0% | 10053.0 | 81.0 |
| length-8192-walking-end-direct | 0/8 | 0.0% | 9947.0 | 31.0 |
| length-8192-walking-end-checks | 8/8 | 100.0% | 10053.0 | 81.0 |
| longtransfer-wash-512-start-direct | 0/5 | 0.0% | 1024.0 | 31.0 |
| longtransfer-wash-512-start-checks | 5/5 | 100.0% | 1130.0 | 81.0 |
| longtransfer-wash-512-end-direct | 0/5 | 0.0% | 1024.0 | 31.0 |
| longtransfer-wash-512-end-checks | 5/5 | 100.0% | 1130.0 | 81.0 |
| longtransfer-wash-4096-start-direct | 0/5 | 0.0% | 5863.0 | 31.0 |
| longtransfer-wash-4096-start-checks | 5/5 | 100.0% | 5969.0 | 81.0 |
| longtransfer-wash-4096-end-direct | 0/5 | 0.0% | 5863.0 | 31.0 |
| longtransfer-wash-4096-end-checks | 5/5 | 100.0% | 5969.0 | 81.0 |
| longtransfer-inspection-512-start-direct | 0/5 | 0.0% | 1026.0 | 31.0 |
| longtransfer-inspection-512-start-checks | 5/5 | 100.0% | 1132.0 | 81.0 |
| longtransfer-inspection-512-end-direct | 0/5 | 0.0% | 1026.0 | 31.0 |
| longtransfer-inspection-512-end-checks | 5/5 | 100.0% | 1132.0 | 81.0 |
| longtransfer-inspection-4096-start-direct | 0/5 | 0.0% | 5865.0 | 31.0 |
| longtransfer-inspection-4096-start-checks | 5/5 | 100.0% | 5971.0 | 81.0 |
| longtransfer-inspection-4096-end-direct | 0/5 | 0.0% | 5865.0 | 31.0 |
| longtransfer-inspection-4096-end-checks | 5/5 | 100.0% | 5971.0 | 81.0 |
| longtransfer-pickup-512-start-direct | 5/5 | 100.0% | 1031.0 | 31.0 |
| longtransfer-pickup-512-start-checks | 5/5 | 100.0% | 1137.0 | 81.0 |
| longtransfer-pickup-512-end-direct | 5/5 | 100.0% | 1031.0 | 31.0 |
| longtransfer-pickup-512-end-checks | 5/5 | 100.0% | 1137.0 | 81.0 |
| longtransfer-pickup-4096-start-direct | 5/5 | 100.0% | 5870.0 | 31.0 |
| longtransfer-pickup-4096-start-checks | 5/5 | 100.0% | 5976.0 | 81.0 |
| longtransfer-pickup-4096-end-direct | 5/5 | 100.0% | 5870.0 | 31.0 |
| longtransfer-pickup-4096-end-checks | 5/5 | 100.0% | 5976.0 | 81.0 |
| longtransfer-supplies-512-start-direct | 5/5 | 100.0% | 1030.0 | 31.0 |
| longtransfer-supplies-512-start-checks | 5/5 | 100.0% | 1136.0 | 81.0 |
| longtransfer-supplies-512-end-direct | 5/5 | 100.0% | 1030.0 | 31.0 |
| longtransfer-supplies-512-end-checks | 5/5 | 100.0% | 1136.0 | 81.0 |
| longtransfer-supplies-4096-start-direct | 5/5 | 100.0% | 5869.0 | 31.0 |
| longtransfer-supplies-4096-start-checks | 5/5 | 100.0% | 5975.0 | 81.0 |
| longtransfer-supplies-4096-end-direct | 5/5 | 100.0% | 5869.0 | 31.0 |
| longtransfer-supplies-4096-end-checks | 5/5 | 100.0% | 5975.0 | 81.0 |
| count-straberry-plain | 10/10 | 100.0% | 430.0 | 95.0 |
| count-straberry-spaced | 10/10 | 100.0% | 436.0 | 95.0 |
| count-straberry-algorithm | 9/10 | 90.0% | 444.0 | 95.0 |
| count-strawberry-plain | 0/10 | 0.0% | 431.0 | 95.0 |
| count-strawberry-spaced | 10/10 | 100.0% | 437.0 | 95.0 |
| count-strawberry-algorithm | 0/10 | 0.0% | 445.0 | 95.0 |
| count-strawberries-plain | 0/10 | 0.0% | 431.0 | 95.0 |
| count-strawberries-spaced | 0/10 | 0.0% | 439.0 | 95.0 |
| count-strawberries-algorithm | 0/10 | 0.0% | 445.0 | 95.0 |
| count-raspberry-plain | 0/10 | 0.0% | 431.0 | 95.0 |
| count-raspberry-spaced | 10/10 | 100.0% | 436.0 | 95.0 |
| count-raspberry-algorithm | 0/10 | 0.0% | 445.0 | 95.0 |
| count-blueberry-plain | 0/10 | 0.0% | 431.0 | 95.0 |
| count-blueberry-spaced | 0/10 | 0.0% | 436.0 | 95.0 |
| count-blueberry-algorithm | 0/10 | 0.0% | 445.0 | 95.0 |
| count-cherry-plain | 10/10 | 100.0% | 429.0 | 95.0 |
| count-cherry-spaced | 10/10 | 100.0% | 433.0 | 95.0 |
| count-cherry-algorithm | 10/10 | 100.0% | 443.0 | 95.0 |
| count-banana-plain | 1/10 | 10.0% | 428.0 | 95.0 |
| count-banana-spaced | 10/10 | 100.0% | 433.0 | 95.0 |
| count-banana-algorithm | 0/10 | 0.0% | 442.0 | 95.0 |
| count-river-plain | 10/10 | 100.0% | 428.0 | 95.0 |
| count-river-spaced | 10/10 | 100.0% | 432.0 | 95.0 |
| count-river-algorithm | 10/10 | 100.0% | 442.0 | 95.0 |
| count-error-plain | 0/10 | 0.0% | 428.0 | 95.0 |
| count-error-spaced | 0/10 | 0.0% | 432.0 | 95.0 |
| count-error-algorithm | 0/10 | 0.0% | 442.0 | 95.0 |
| count-rrr-plain | 10/10 | 100.0% | 429.0 | 95.0 |
| count-rrr-spaced | 10/10 | 100.0% | 430.0 | 95.0 |
| count-rrr-algorithm | 10/10 | 100.0% | 443.0 | 95.0 |
| count-r-plain | 10/10 | 100.0% | 428.0 | 95.0 |
| count-r-spaced | 10/10 | 100.0% | 428.0 | 95.0 |
| count-r-algorithm | 10/10 | 100.0% | 442.0 | 95.0 |
| count-rrrrrr-plain | 7/10 | 70.0% | 430.0 | 95.0 |
| count-rrrrrr-spaced | 10/10 | 100.0% | 433.0 | 95.0 |
| count-rrrrrr-algorithm | 8/10 | 80.0% | 444.0 | 95.0 |
| count-abracadabra-plain | 10/10 | 100.0% | 430.0 | 95.0 |
| count-abracadabra-spaced | 0/10 | 0.0% | 438.0 | 95.0 |
| count-abracadabra-algorithm | 10/10 | 100.0% | 444.0 | 95.0 |
| count-qrzrpr-plain | 4/10 | 40.0% | 431.0 | 95.0 |
| count-qrzrpr-spaced | 0/10 | 0.0% | 433.0 | 95.0 |
| count-qrzrpr-algorithm | 1/10 | 10.0% | 445.0 | 95.0 |
| count-rrabr-plain | 10/10 | 100.0% | 429.0 | 95.0 |
| count-rrabr-spaced | 0/10 | 0.0% | 432.0 | 95.0 |
| count-rrabr-algorithm | 10/10 | 100.0% | 443.0 | 95.0 |
| count-RrR-plain | 10/10 | 100.0% | 430.0 | 95.0 |
| count-RrR-spaced | 10/10 | 100.0% | 430.0 | 95.0 |
| count-RrR-algorithm | 10/10 | 100.0% | 444.0 | 95.0 |
| described-wash-0 | 10/10 | 100.0% | 356.0 | 31.0 |
| described-wash-1 | 10/10 | 100.0% | 356.0 | 31.0 |
| described-tires-0 | 10/10 | 100.0% | 358.0 | 31.0 |
| described-tires-1 | 10/10 | 100.0% | 358.0 | 31.0 |
| described-inspection-0 | 10/10 | 100.0% | 358.0 | 31.0 |
| described-inspection-1 | 10/10 | 100.0% | 358.0 | 31.0 |
| described-oil-0 | 10/10 | 100.0% | 358.0 | 31.0 |
| described-oil-1 | 10/10 | 100.0% | 358.0 | 31.0 |
| described-weigh-0 | 10/10 | 100.0% | 359.0 | 31.0 |
| described-weigh-1 | 10/10 | 100.0% | 359.0 | 31.0 |
| described-trade-0 | 4/10 | 40.0% | 360.0 | 31.0 |
| described-trade-1 | 1/10 | 10.0% | 360.0 | 31.0 |
| described-pickup-0 | 10/10 | 100.0% | 363.0 | 31.0 |
| described-pickup-1 | 10/10 | 100.0% | 363.0 | 31.0 |
| described-job-0 | 10/10 | 100.0% | 358.0 | 31.0 |
| described-job-1 | 10/10 | 100.0% | 358.0 | 31.0 |
| described-receipt-0 | 10/10 | 100.0% | 371.0 | 31.0 |
| described-receipt-1 | 10/10 | 100.0% | 371.0 | 31.0 |
| described-supplies-0 | 10/10 | 100.0% | 362.0 | 31.0 |
| described-supplies-1 | 10/10 | 100.0% | 362.0 | 31.0 |
| described-refund-0 | 10/10 | 100.0% | 363.0 | 31.0 |
| described-refund-1 | 10/10 | 100.0% | 363.0 | 31.0 |
| described-mobile-0 | 10/10 | 100.0% | 371.0 | 31.0 |
| described-mobile-1 | 10/10 | 100.0% | 371.0 | 31.0 |
| described-brakes-0 | 10/10 | 100.0% | 364.0 | 31.0 |
| described-brakes-1 | 10/10 | 100.0% | 364.0 | 31.0 |
| described-alignment-0 | 10/10 | 100.0% | 363.0 | 31.0 |
| described-alignment-1 | 10/10 | 100.0% | 363.0 | 31.0 |
| described-windscreen-0 | 10/10 | 100.0% | 362.0 | 31.0 |
| described-windscreen-1 | 10/10 | 100.0% | 362.0 | 31.0 |
| described-paint-0 | 10/10 | 100.0% | 362.0 | 31.0 |
| described-paint-1 | 10/10 | 100.0% | 362.0 | 31.0 |
| described-keys-0 | 8/10 | 80.0% | 359.0 | 31.0 |
| described-keys-1 | 0/10 | 0.0% | 359.0 | 31.0 |
| described-interview-0 | 10/10 | 100.0% | 352.0 | 31.0 |
| described-interview-1 | 10/10 | 100.0% | 352.0 | 31.0 |
| described-manual-0 | 10/10 | 100.0% | 365.0 | 31.0 |
| described-manual-1 | 10/10 | 100.0% | 365.0 | 31.0 |
| described-office-0 | 10/10 | 100.0% | 362.0 | 31.0 |
| described-office-1 | 10/10 | 100.0% | 362.0 | 31.0 |
| distance-absent | 20/20 | 100.0% | 315.0 | 31.0 |
| distance-walk5 | 0/20 | 0.0% | 327.0 | 31.0 |
| distance-drive5 | 20/20 | 100.0% | 327.0 | 31.0 |
| distance-meters100 | 2/20 | 10.0% | 327.0 | 31.0 |
| distance-km50 | 20/20 | 100.0% | 326.0 | 31.0 |
| replicate-inline-direct | 0/25 | 0.0% | 327.0 | 31.0 |
| replicate-inline-goal | 14/25 | 56.0% | 338.0 | 31.0 |
| replicate-state-direct | 0/25 | 0.0% | 327.0 | 31.0 |
| replicate-state-goal | 0/25 | 0.0% | 338.0 | 31.0 |
| countfollow-straberry-inline-original | 0/15 | 0.0% | 426.0 | 95.0 |
| countfollow-straberry-inline-explicit | 14/15 | 93.3% | 427.0 | 95.0 |
| countfollow-straberry-state-original | 0/15 | 0.0% | 429.0 | 95.0 |
| countfollow-straberry-state-explicit | 15/15 | 100.0% | 430.0 | 95.0 |
| countfollow-strawberry-inline-original | 0/15 | 0.0% | 424.0 | 95.0 |
| countfollow-strawberry-inline-explicit | 0/15 | 0.0% | 425.0 | 95.0 |
| countfollow-strawberry-state-original | 0/15 | 0.0% | 430.0 | 95.0 |
| countfollow-strawberry-state-explicit | 0/15 | 0.0% | 431.0 | 95.0 |
| evidence-none | 0/20 | 0.0% | 327.0 | 31.0 |
| evidence-facts | 20/20 | 100.0% | 356.0 | 31.0 |
| evidence-previous_answers | 20/20 | 100.0% | 357.0 | 31.0 |
