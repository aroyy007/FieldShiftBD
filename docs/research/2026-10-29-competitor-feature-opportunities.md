# FieldShift BD: competitor evidence and feature opportunities

Reviewed 2026-10-29, Asia/Dhaka. Research/recommendations only; no application or implementation-plan changes. Companion [repository research](2026-10-29-competitor-repositories.md) covers seven additional related projects. This synthesis adds the user's two live sites and distinguishes current FieldShift BD code from the [full planned scope](../plans/2026-10-29-nasa-planting-window-and-rotation.md).

## Finding

Multilingual voice, NASA maps, rotation ranking, historical replay, printable reports and climate sliders already appear across this sample. Many also already appear in our full plan. They remain useful requirements, but should not be presented as extraordinary new additions.

The strongest additional story is: **the app knows when its recommendation depends on missing information, asks one useful question, explains how far a chosen plan can tolerate change, and offers a confirmed fallback when conditions cross a supported limit.** This extends our existing M1 intake, M2 advisor, M3 tasks, M4 environmental evidence and M5 chat without inventing another product module.

This is a bounded sample of publicly available work, not proof of worldwide novelty. Proposed score benefits are our assessment against the supplied criteria, not a guaranteed award or a predicted score. Public demos and models do not establish field effectiveness.

## Directly inspected user-supplied sites

### CropSafe

- [Live site](https://cropsafe.neonweb.xyz/), exact matching [repository](https://github.com/FahadIslam09/fieldshift). Do not confuse this with the unrelated funded company sharing the CropSafe name.
- Inspected the home, recommendation and in-season advisory screens using the supplied Tanore sample. The UI offers crop alternatives, estimated pump/fuel savings, a planting calendar, AWD guidance, heat-stage protection and post-harvest relay-crop preparation.
- Source snapshot: `649f3115aa37f0de6af051d61bb0f4166a1c4607`. [Calendar implementation](https://github.com/FahadIslam09/fieldshift/blob/649f3115aa37f0de6af051d61bb0f4166a1c4607/src/lib/calendar-optimizer.ts) sets crop/zone window shifts and safety percentages from fixed configuration; the reviewed function is not calculating a 25-year rainfall-distribution shift. [EcoCrop implementation](https://github.com/FahadIslam09/fieldshift/blob/649f3115aa37f0de6af051d61bb0f4166a1c4607/src/lib/ecocrop.ts) combines heuristics and fixed water/cost assumptions. [NASA adapter](https://github.com/FahadIslam09/fieldshift/blob/649f3115aa37f0de6af051d61bb0f4166a1c4607/src/services/nasa-power.ts) has a live POWER request and fallback telemetry. [Advisory screen](https://github.com/FahadIslam09/fieldshift/blob/649f3115aa37f0de6af051d61bb0f4166a1c4607/src/app/advisory/page.tsx) contains fixed agronomic/savings text. No field-outcome validation was performed here.
- Lesson: actionable farmer units and standing-crop versus next-crop flows communicate clearly. Our advantage must come from source-backed applicability and reproducible calculations, rather than copying displayed protection/saving percentages or fixed planting shifts.

### Samuel's FieldShift

- [Live app](https://samuelakosaonyejekwe.github.io/fieldshift/), [repository](https://github.com/samuelakosaonyejekwe/fieldshift).
- Opened the Bogura demo, recommendation screen and a plan detail. Observed historical-year replay, current-rotation comparison, climate lenses, soil/water/income indicators, month-level tasks, calendar export, report/share controls and an offline-readiness display. Did not independently test airplane mode, generated exports, language accuracy or voice output.
- Source snapshot: `8a8b8be0f603dde3e5c6312da9280eff55f38299`. [engine.js](https://github.com/samuelakosaonyejekwe/fieldshift/blob/8a8b8be0f603dde3e5c6312da9280eff55f38299/js/engine.js) implements placement, heuristic suitability, historical replay, soil/economic calculations and a named failure threshold. [Data adapter](https://github.com/samuelakosaonyejekwe/fieldshift/blob/8a8b8be0f603dde3e5c6312da9280eff55f38299/js/data.js) and [service worker](https://github.com/samuelakosaonyejekwe/fieldshift/blob/8a8b8be0f603dde3e5c6312da9280eff55f38299/sw.js) are separate inspection entry points; no independent field validation is established by the observed outputs.
- Lesson: a historical playback is already a competitive baseline. Local agronomic validity, unknown-input handling and operational follow-through are stronger opportunities than matching the number of languages or long-horizon numerical projections.

## Additional related projects

| Project | Useful idea | Evidence/status limit |
|---|---|---|
| [CropShift](https://github.com/Taaanha/Crop-Shift) | Similar historical-year selection, replay, data receipts | Repository-described 2026 capability; implementation retrieval was unavailable in this review |
| [RotaShift](https://github.com/XtremeseOISHEE/RotaShift) | Calendar adaptation margin and household priorities | 2026 interactive prototype explicitly uses sample values; not field-validated robustness |
| [Sky2Root](https://github.com/spaul571/sky2root) | Day-by-day season replay and extension-agent triage | 2026 prototype separates real imagery/NDVI from seeded illustrative outcomes |
| [Space Hunters](https://github.com/AhmedSalah-26/space-hunters) | Three-season matrix, guided presentation and exports | 2026 source has actual POWER access, but inspected scoring uses heuristic increments |
| [BoponX](https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026) | Evidence gates and printable preparation plan | 2026 source distinguishes calendar-source availability from encoded recommendation authority |
| [AgriGuard](https://github.com/ESR-style/AgriGuard) | Irrigation and river-risk action views | 2024 related precedent; reviewed implementation includes demonstration thresholds |
| [WaterWise](https://www.spaceappschallenge.org/nasa-space-apps-2024/find-a-team/gaamaramma/?tab=project) | ET/rain inputs → practical seven-day irrigation schedule | 2024 precedent, not current competitor; [NASA confirms its Best Use of Data award](https://www.nasa.gov/learning-resources/stem-engagement-at-nasa/nasa-international-space-apps-challenge-announces-2024-global-winners/). Do not assume its OpenET coverage extends to Bangladesh |

Detailed source files and individual limitations are in the companion report. The first seven projects including the two supplied sites describe themselves as 2026 Field Shift work; this review does not verify every team's registration, final submission or eligibility.

## What is already in our scope

Existing code includes farm profiles/resources, multi-farm accounts, farm-scoped conversations, tasks/problems/check-ins, weather integration and disease analysis. Some supporting agronomic knowledge remains incomplete.

Our new full plan already requires onset/GDD and two-period comparison, three rotations, climate/scenario controls, map/timeline, uncertainty/provenance, Bangla/English voice/tap UX and offline behavior. None should be reintroduced as a newly discovered feature. New suggestions below are incremental extensions; the required scientific and lifecycle gates remain first.

## Ranked additions

Effort is a relative engineering assessment, assuming sourced calendars, typed results and core integration already exist. It is not a delivery-time guarantee.

### 1. Conditional Plan B with an explicit switch reason

**New behavior:** each selected rotation carries a versioned contingency policy: relevant observations, latest feasible dates, supported alternatives and which changes require a fresh farmer decision. If updated evidence makes the current plan infeasible, the app offers the changed plan and task diff, not merely a generic weather alert.

Illustrative UI, not an actual recommendation: “প্রয়োজনীয় বৃষ্টি নির্ধারিত সময়ের মধ্যে না এলে এই পরিকল্পনা বদলাতে হবে। বিকল্পটি দেখুন।” The interface distinguishes “observation missing”, “condition met”, “needs field confirmation” and “alternative unsupported”.

**Why it adds value:** the current plan has alerts/confirmation but not an explicit saved per-rotation fallback policy. This makes the assistant useful after its first recommendation and creates a clear demonstration for relevance, UX and presentation.

**Implementation fit:** M4 supplies dated evidence, M2 evaluates the policy, M3 owns operational state/tasks and M5 presents an explicit confirm card. No automatic crop switch, repeated-task creation or use of old cached data as a fresh trigger. Forecast probability and historical tendency do not become an observed event.

**Proof:** correct switching/non-switching under dated fixtures; expired/contradictory evidence cannot trigger execution; one confirmation applies once; no completed task is silently overwritten; next chat sees the updated plan.

### 2. Ask the field question that changes the decision

**New behavior:** test a small set of source-supported plausible values for an unknown input, such as irrigation availability, drainage or a measured soil parameter. If an answer changes feasibility or ranking, ask that question before pretending one option is best. Show when several options remain plausible.

Illustration: “এই জমিতে প্রয়োজনের সময় সেচ পাওয়া যায়?” If a lab-only fact is required, do not ask the farmer to guess it. Show the needed measurement and an evidence-limited result. If coarse satellite moisture and a farmer's field report disagree, retain both with their scales/times and request a useful observation instead of averaging the conflict away.

**Why it adds value:** our plan lists missing information; this chooses the next question based on its decision impact. It can extend existing M1 progressive onboarding and M2 evidence gates with modest infrastructure.

**Implementation fit:** M2 performs deterministic feasible-set/sensitivity analysis, M1 persists confirmed profile facts/provenance and M5 asks one short Bangla question. A transparent rule-based approach does not need a paid LLM or a claimed calibrated Bayesian probability.

**Proof:** the selected question actually changes or narrows the supported alternatives on test cases; irrelevant questions are not asked; unknown values stay unknown and corrections propagate across all scoped views.

### 3. Rotation robustness margin with a binding constraint

**New behavior:** report the bounded delay/water/heat scenario range in which each rotation still fits its sourced calendar/resource rules, where it becomes infeasible, and which crop/stage is binding. Return a validated range or no result rather than a universal “safe percentage”.

**Novelty limit:** RotaShift already shows this interaction with sample values. It is new to our explicit result contract, not a new invention. Our opportunity is a reproducible calculation, uncertainty and direct connection to the conditional fallback and M3 tasks.

**Implementation fit:** M2 sweeps a documented scenario range using M4 environmental features and local calendars; frontend shows one understandable margin and an expandable explanation. It is a calendar/resource feasibility test, not a yield forecast or crop-survival guarantee. Photoperiod/variety and nursery timing remain constraints.

**Proof:** hand-calculated feasible/infeasible boundaries, non-monotonic/disjoint feasible ranges, crop overlaps and unknown data. Do not use a monotonic search if the agronomic rules do not guarantee monotonicity.

### 4. Household rice needs plus a multi-farm cropping allocation

**New behavior:** farmer declares a minimum staple-production target or a minimum area to retain for rice, alongside a resource ceiling. Compare allocation across their saved farms instead of replacing every rice field with the most profitable modeled alternative.

This goes beyond priority sliders and per-farm recommendations in our current plan. It represents a practical Bangladesh smallholder constraint. Where reliable yield ranges are unavailable, use an explicitly farmer-selected rice-area floor; never promise household food security from uncertain yield estimates. Area floors are not equivalent to nutritional security.

**Implementation fit:** M1 owns declared constraints and M2 calculates candidate allocations. Keep each farm's selected plan and M3 state distinct. Show assumed price/yield ranges and residual risk instead of guaranteed cash return.

**Proof:** total area/resource conservation, supported local crops, no invented yields, uncertainty near the target and explicit infeasibility when all constraints cannot be met.

**Novelty limit:** RotaShift mentions household priorities, so the potentially distinctive part is explicit multi-farm allocation with a declared floor, not merely a household-themed label. This needs more work than the first three.

### 5. Shared pump scheduling across the farmer's own farms

**New behavior:** enter a pump's measured flow or documented range, allowed hours, delivery efficiency and farm access; compare overlapping irrigation requests and propose feasible slots across saved farms. Indicate when available capacity cannot support a rotation and offer a sourced alternative.

CropSafe displays pump-time/cost advice and WaterWise describes irrigation schedules. The additional opportunity is capacity-aware coordination across farms. No prominent equivalent was established in this inspected sample; that is not a global absence claim.

**Implementation fit:** first restrict to one farmer's existing account. M1 holds resource facts, M2 evaluates capacity/rotation feasibility, M3 owns confirmed schedules. Multi-household sharing would require explicit authorization/privacy design and is a larger subsequent step. No IoT hardware is required for a declared-capacity pilot.

**Proof:** no overlapping reservations on one pump, compatible deadlines, correct area/volume/flow/efficiency units, bounded uncertainty, manual override, cancelled jobs and repeated confirmations. Do not infer hours from satellite moisture alone.

### 6. Why the preferred crop was rejected, and the smallest supported change

**New behavior:** answer a farmer's intended-crop question with the binding constraint and permitted changes that restore feasibility: another locally supported variety, date or declared resource arrangement. If none is supported, say so.

This is an extension of planned factor explanations and scenario controls, not wholly new science. It can be implemented alongside the next-question feature. It must not recommend purchasing/borrowing resources or precise financial returns without evidence and an explicit user decision.

### 7. Link each recommendation to later observed outcomes

Existing season history is reused, but add a view linking the original result/method/cache version to actual farmer-entered planting/harvest dates, water-use records and failure reasons. Optional consented small comparison plots can provide measured timing feedback.

This is a useful longer-term differentiator in scientific credibility. A single season or observational comparison cannot prove causal yield/water benefits. For the hackathon, show a clearly labeled synthetic logic fixture and a real small usability session; do not label fixture outcomes as farmer validation.

## Recommended scope selection

After the required organizer/science/lifecycle flow works, implement the linked first three: **robustness margin → one useful field question → confirmed conditional Plan B**. The user sees a coherent decision journey rather than three isolated extras. If only a small extension is affordable, start with next-question/minimal-change reasoning over already sourced rules.

Consider the rice-area allocation and shared-pump scheduler after measuring the first journey. Their local relevance is strong, but they require additional data/constraint validation and must not delay required onset/statistics/rotation correctness.

More languages, another chatbot, a 3D globe or a “NASA verified” badge are weak principal differentiators in this sample. NASA award participation is not an endorsement of generated recommendations. Preserve attribution and check actual code/model/data licenses before reusing any material; ideas can be independently implemented without copying assets or unlicensed code.

## Demonstration to prioritize

1. Open one real supported farm/district/crop with a source-backed rotation comparison.
2. Show uncertainty about a field resource; the app asks one concrete question that affects the feasible set.
3. Answer with a confirmed farmer-observable fact; show the revised choice and the reason.
4. Show the calendar/resource condition beyond which it no longer fits and the supported contingency.
5. Introduce a clearly labeled updated observation/scenario. The app proposes the precise task/plan change; farmer confirms once and sees it in the existing scoped chat/tasks.
6. Show sources, uncertainty and the unsupported-case fallback. Measure understandable Bangla task completion on an actual phone.

This supports validity, relevance, UX and presentation. It does not guarantee winning; quality of scientific evidence and a working complete flow remain decisive inputs to the judges.
