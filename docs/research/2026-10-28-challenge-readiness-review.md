# FieldShift BD: challenge alignment and voice feasibility review

Reviewed 2026-10-28, Asia/Dhaka. Baseline: local `Aveshek` / `origin/main`, commit `1077a06`.

This is an advisory review, not implementation authorization. Existing plans, module contracts and application code were not changed. Evidence is source inspection and current official documentation; the application, phone speech engines, database contents and tests were not executed for this review. Existing test files do not establish that the current release passes them.

## Decision

- A constrained Android APK with device Bangla speech, system TTS, a deterministic advisor and an online backend can be developed with free tools and piloted within available resources.
- A dependable, indefinitely zero-cost production service across backend, database, ML, speech, distribution, backups and support is not established. Open-source licensing is different from free compute; free hosting has capacity, availability and retention restrictions.
- The largest challenge gap is multi-season rotation decision support using NASA observations. Voice improves accessibility but cannot replace that scientific capability.
- Complete verified season knowledge and a small, reproducible NASA-driven rotation comparison before implementing the entire voice roadmap.

## Challenge and judging interpretation

The supplied final statement matches the description indexed on the [official challenge page](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/): NASA Earth observations, local soil information, crop characteristics and farmer priorities should support exploration of resilient rotation strategies. The brief suggests, rather than mandates, comparing at least three strategies including the current rotation. That is nevertheless a strong minimum demonstration target.

The supplied image shows criteria 3-11: validity, relevance, presentation, teamwork, user experience, NASA data use, challenge identification, public repository and completed project page. Criteria 1-2 are cropped out; do not invent their names, weights or a predicted overall score. Treat the displayed local bonus and 118-point total as supplied event guidance, not independently verified universal NASA scoring rules.

## Current implementation evidence

| Area | Source-level status and limitation |
|---|---|
| M1 | Password registration/login, Argon2id, bearer authentication, owner-scoped farms, location and editable resources are implemented. Native release validation is still required. |
| Frontend | Expo 57 / RN 0.86, backend services for M1-M6, farm-specific chat, tasks, alerts, crop advisor and scanning screens exist. Imports from `data/demo.ts` include types; that alone does not mean the application uses demo records. Preview paths must remain clearly separated from real-user flows. |
| M2 | Explainable evidence-gated crop recommendations, season lifecycle and harvest APIs exist. `backend/M2_GUIDE.md:286` documents four catalog crops and 245 varieties, narrow potato/wheat soil-land advice, duration evidence and regional zoning. Regional zoning is explicitly not individual-field suitability. |
| Critical M2 data blocker | The shipped evidence supplies no verified season plans, growth stages or initial task definitions for any crop. Plan creation returns a conflict without matching approved knowledge. New real-user flows therefore cannot assume season activation succeeds. Check a clean imported database, not only prepopulated demo seasons. |
| M3 | Task/problem/check-in and current-state services exist. Their usefulness depends on an actual active season and verified M2 plan. |
| M4 | Open-Meteo forecast and a 30-day NASA POWER history window are fetched. `weather_suppression.py` explicitly uses forecast, not NASA history, to trigger actions. NASA is currently contextual rather than integrated into rotation decisions. Threshold provenance explicitly calls defaults demo placeholders. |
| M5 | Farm-context aggregation, some Bangla intent keywords, Gemini calls and deterministic fallback responses exist. Fallback prose is mostly English. `ChatResponse` has suggested action strings, not the proposed structured confirmation/execution contract. |
| M6 | A local ~296 MB checkpoint is present in this workspace, but is ignored and is not guaranteed in a fresh deployment. The model card declares CC BY-NC 4.0. Possible-disease analysis automatically creates/reuses an M3 Problem; the voice plan's confirmation-before-problem flow disagrees with this behavior. |
| Voice/offline | No voice dependencies, speech implementation, Bangla translation framework, persisted farm cache or action outbox were found in the inspected application. Secure token storage already exists and should be reused. |
| Release | App name/scheme remain `frontend`. API defaults to `127.0.0.1`, which refers to the phone when running a native app. Compose publishes Postgres with trust authentication; backend starts with `--reload`. These are development settings. |

Evidence paths: `frontend/package.json`, `frontend/app.json`, `frontend/src/context/AppProvider.tsx`, `frontend/src/services/api-client.ts`, `backend/app/core/security.py`, `backend/M2_GUIDE.md`, `backend/app/services/{m2_advisor,weather_providers,weather_suppression,weather_thresholds,chat_engine,disease_inference}.py`, `backend/app/schemas/chat.py`, `backend/app/api/routes_disease.py`, `backend/model/README.md`, `docker-compose.yml`, `backend/Dockerfile`.

## Changes needed in the voice proposal before implementation

1. Replace the historical repository status section. Auth, API integration and module services already exist. Reuse their routes and contracts; do not build parallel auth/chat/state systems from the proposed filenames.
2. Keep Android device STT + system TTS as the first experiment, with capability checks, privacy disclosure, tap fallback and no background listening. Do not promise Bengali offline recognition or iOS Bengali STT without actual device capability results. The speech library's `getSupportedLocales()` is unavailable on Android 12 and below; use an availability/attempt/error fallback on those devices instead of the plan's unconditional locale-query spike.
3. Use a native development/release build and physical Android phones. Chrome responsive view cannot verify native permissions, speech services, audio interruption, low-memory behavior or lifecycle cancellation.
4. Start with a small set of recorded prompts, navigation, a spoken rotation explanation and task reading. Defer widgets, broad dialect training, custom speech hosting and automatic voice writes until the core challenge flow works.
5. Reconcile M6 auto-problem persistence with confirmation. A confirmation card after calling the present scan endpoint cannot prevent its existing write. Owners must agree the desired contract first; do not silently override M6.
6. Scope confirmation precisely. Chat logging and necessary internal records are writes too; distinguish user-commanded farm changes from permitted technical logging. Explicitly confirm farm, target, changed values and expiry, and revalidate ownership/current state at execution.
7. Persistent actions need client request IDs, replay protection, farm/season scope, version/conflict checks, expiry and exact-once effect semantics. An app-only confirm flag is insufficient. Log out must isolate/delete the prior user's queued data. Do not replay a stale irrigation action days later.
8. Device STT may expose only text. Do not promise a recoverable recording, an audio upload queue, a level meter or reliable confidence values unless the adapter actually supplies them. Add raw recording only for an explicit requirement with consent.
9. Replace broad platform absolutes and anecdotal exclusions with current compatibility tests. A report of small Whisper producing the wrong script is not evidence that every small checkpoint must always be rejected. Verify every specific checkpoint, conversion and dataset license.
10. Treat the proposed multi-region evaluation and 3-4-week pilot as post-MVP research. A smaller consented test can support a hackathon claim if sample size, devices, noise conditions and limitations are honestly reported. Free volunteer development does not remove electricity, data, hardware and support costs.
11. Clarify Bangla ambiguity: `কাল`, local bigha conversion, numbers, crop aliases, multiple farms, and the difference between voice comprehension confidence and agronomic certainty. Ask a short clarification rather than committing a guess.

## Highest-value additions, in order

### 1. Unblock a complete real farm season

Choose one agricultural locality and a manageable, source-supported crop set. Add verified planting windows, stage durations, task definitions, harvest windows and applicability limits. Include at least one suitable legume/cover alternative only after obtaining local evidence; the existing four-crop catalog alone is not enough to claim validated soil-restoring rotation choices. Use existing M1 catalog and M2 evidence mechanisms with the relevant owners.

Acceptance: fresh database -> reference import -> register -> save farm -> supported recommendation -> select crop -> generate/activate plan -> M3 tasks -> farm-context chat. No hand-written production DB inserts or synthetic agronomic advice.

### 2. Make NASA data affect rotation comparison

Implement an M2-owned rotation exploration service consuming a read-only historical climate feature contract from the appropriate data/weather owner. Retain M3 as the operational-state owner. A separate exploration scenario is not an active season until the farmer selects and confirms it.

Recommended inputs: full existing rotation rather than only the last crop; planting/harvest dates; soil/land type; irrigation/water source; relevant locally measured soil properties with provenance; equipment, budget and priorities. Missing soil measurements remain unknown.

Recommended outputs: current rotation plus two locally supported alternatives, represented over a common multi-season calendar. Explain water-demand category, dry-spell/heat exposure, bare-soil periods, crop-family repetition, potential legume/soil-cover benefits, resource/calendar compatibility, evidence references and uncertainty. Hard constraints exclude infeasible options before ranking. Let farmer priorities change the tradeoffs; show factors instead of presenting one opaque score as truth.

Use a suitable historical baseline, for example 2001-2025 where coverage is adequate, with missing-data handling and documented seasonal aggregation. That is a historical reference distribution, not automatically a WMO climate normal or a prediction of next year's weather. Historical replay/backtesting can compare exposure under past years; it does not prove yield or water savings.

NASA POWER is an accessible starting source for temperature and meteorological context. Add GPM IMERG rainfall if time permits a correct, reproducible ingestion path; one well-used NASA source is preferable to many decorative integrations. POWER meteorology is model assimilation/reanalysis, not a sensor measuring this individual farm. Preserve native product grid, source version, units, period and quality information. Interpolating a coarse grid does not create field-scale knowledge.

Use rainfall/dry spells as exposure indicators, not measured root-zone moisture. Quantitative water-demand claims require defensible calculations and crop parameters, e.g. FAO-56 ET0/Kc with a properly specified water balance. Do not label rainfall minus ET as measured soil moisture, or omit paddy-specific losses while claiming precise rice irrigation savings.

Acceptance: changing a relevant NASA input changes a traceable comparison factor; results are reproducible from pinned inputs; removing NASA changes result availability/confidence; missing data is never converted into zero rainfall. If alternatives legitimately tie, explain the tie rather than forcing different scores.

### 3. Show a farmer-readable evidence trail

Add a compact 'কেন এই পরামর্শ?' view and spoken summary: observation period, source, comparison to baseline, crop/soil rule, expected tradeoff, uncertainty and farmer decision. Keep technical dataset details in an expandable evidence view. Distinguish observed, forecast, simulated and farmer-reported values visibly. Avoid fabricated yield, profit, carbon or water-saving percentages.

### 4. Add a narrow, reliable Bangla voice experience

Implement Bangla text for the core journey plus Android tap-to-speak, short spoken answer, replay, clear mic state and denial/offline fallback. Suggested first commands: show farms, compare rotations, explain why, today's tasks, replay, go back. Read-only voice is a useful initial release. Farm changes follow confirmed structured actions through owning modules.

Preserve sign-in -> all farms, and select farm -> farm-specific chat. A spoken daily summary must not silently select the wrong farm or replace the established entry flow.

### 5. Harden public deployment

Set a stable HTTPS API URL at build time; configure app ID/name, release signing and permission texts; keep secrets server-side. Use a production server command, password-authenticated non-public DB, migrations, reproducible reference imports, durable backups and restore checks. Add login throttling, appropriate session expiry/revocation/recovery and privacy controls for shared phones. No production secrets should be printed during review or copied into the app.

Preserve graceful behavior for unavailable NASA, forecast, LLM, model weights and network. Use source-dated cached data with visible staleness. A demo cache is not an excuse to represent cached observations as live. A free-tier backend unable to host PyTorch can omit the optional M6 feature from that deployment or move inference to an explicitly provisioned worker; it must not fake a scan result.

## Scientific and safety issues to resolve

- M4 thresholds currently declare themselves demonstration values. Source/tune them for the supported crop/stage and ensure weather advice does not claim rainfall definitely meets water needs without water-balance support.
- M5's no-evidence prompt says 'Standard Bangladesh agricultural guidelines apply.' Replace the implied evidence with an explicit evidence gap and bounded answer behavior. A prompt alone does not enforce grounding. Citation IDs and supported factual outputs should be validated server-side.
- Test whether M5's context filtering matches the full applicability conditions used by M2, not only crop, variety, date and locality. Approved evidence may still be wrong for a particular soil/irrigation context.
- A model's class confidence and training accuracy are not field accuracy, calibrated disease probability or problem severity. Preserve healthy/uncertain/disagreement/repeat-result handling, and validate on held-out locally representative photos before making performance claims.
- The current M6 model's non-commercial restriction conflicts with the voice plan's commercial-use-compatible license policy if that policy is intended project-wide. A noncommercial challenge demo and a later commercial release need separate, accurate license decisions.

## Practical verification gates

1. Clean database and APK golden journey above, including plan activation and M3 task generation.
2. Rotation invariants: date overlap, crop/variety locality, missing data, leap years, unit conversion, same-family rules, resource constraints, source expiry, out-of-region requests and infeasible alternatives.
3. Science: hand-calculated reference cases; held-out historical replay; sensitivity checks; explicit uncertainty and no claimed measured benefits without measurements.
4. Two-account/two-farm isolation, expired authentication, unauthorized IDs, duplicate requests and stale confirmation.
5. Physical Android: Bangla installed/not installed, denied/revoked mic, silence, noisy input, headset, TTS interruption, app backgrounding, restart and poor network.
6. If offline writes are added: survive restart, never cross farmer accounts, preserve farm/season scope, do not duplicate and do not overwrite newer remote changes.
7. Deploy smoke check from a phone on mobile data, rather than localhost/Wi-Fi alone; restore a database backup and test provider quota/outage behavior.

## Judging-focused demonstration

Show one farmer and one actual supported locality. Farmer states a resource constraint; the app compares the current rotation and two alternatives using NASA-derived conditions and sourced local crop facts; farmer hears and opens the explanation, changes a priority, selects a feasible option and sees its scheduled tasks. Show an uncertainty or offline case. Close with measured usability results and an honest account of what remains experimental.

Map evidence directly to the image: reproducible calculations for validity; NASA-dependent rotation reasoning for relevance/data use; a short farmer story for presentation; a working Bangla core journey for UX; contributor/PR ownership for teamwork; exact challenge name, public repo and completed official project page for submission points. Do not manufacture user studies or participation claims. The image does not support a credible predicted winning score.

## Primary sources

- [Official challenge](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/) — current search-indexed description agrees with supplied statement; direct page fetch returned 502 during review.
- [NASA POWER methodology](https://power.larc.nasa.gov/docs/methodology/) and [meteorology sources](https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/) — source/product distinctions.
- [NASA POWER climatology API](https://power.larc.nasa.gov/docs/services/api/temporal/climatology/) — historical summaries and custom periods.
- [NASA POWER tutorials](https://power.larc.nasa.gov/docs/tutorials/) — meteorological grid and provisional-data replacement.
- [NASA GPM IMERG](https://gpm.nasa.gov/data/imerg) and [V07 technical documentation](https://gpm.nasa.gov/sites/default/files/2023-07/IMERG_TechnicalDocumentation_final_230713.pdf) — rainfall estimates, resolutions and processing/latency differences.
- [FAO-56](https://www.fao.org/4/x0490e/x0490e00.htm) — ET0, crop coefficients and water balance.
- [Open-Meteo pricing](https://open-meteo.com/en/pricing) — noncommercial free API, quotas and no uptime guarantee; distinguish the hosted-service terms from data licensing.
- See companion `2026-10-28-free-mobile-voice-feasibility.md` for current speech, hosting and mobile distribution sources and restrictions.
