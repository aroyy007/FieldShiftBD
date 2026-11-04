# Bangladesh End-to-End Farmer Field Support

**Status:** Proposed design for review. No product code or source ingestion is included in this document.

## Intent

Help a farmer anywhere in Bangladesh manage decisions for each field through the crop lifecycle: create a farm profile, choose crops or rotations, plan a season, follow stage-appropriate work, understand weather and risk, and get cautious support when a crop problem appears. The app uses reviewed local agronomy evidence and NASA Earth-observation context where useful. It explains decisions in plain Bangla and English, makes uncertainty visible, and never implies that coarse regional data is a field measurement.

## Goals

- Support the farmer journey from account and field setup through crop selection, season planning, in-season tasks, harvest timing context, and crop-problem support.
- Compare the farmer's recorded rotation, when available, with up to two source-backed alternatives as one part of crop planning.
- Support district, upazila, village/locality, and optional farm-pin locations; label the actual geographic scale of every data source.
- Use BARC/CZIS for regional suitability and crop-pattern context, BRRI and other relevant Bangladesh research sources for crop/sequence/calendar evidence, and BAMIS/DAE for dated weather advisory context.
- Use NASA data only for a defined evidentiary question. Keep each dataset distinct and show its dates, source, spatial scale, retrieval/cache status, and limitations.
- Show missing inputs as unknown, not as a match or mismatch. Return partial results when useful; return insufficient evidence when a defensible comparison cannot be made.
- Keep historical observations, current advisories, and future projections distinct.
- Save a result only on farmer request; keep it private to the farmer and authorized farm collaborators.
- Use simple, accessible farmer-facing language. Present a concise explanation, key trade-offs, a useful next step, and inspectable provenance.
- Keep a field-specific history of crop/season choices and completed work so future advice can use known context without treating missing history as fact.
- Show irrigation, crop-care, and harvest-timing guidance only when supported by a reviewed local crop calendar, crop stage, weather context, and stated assumptions.
- For disease photos, explain the result and uncertainty, offer safe next steps, and connect confirmed problems to the field record with farmer-visible status.
- Present pesticide or treatment guidance only from verified, current, crop- and problem-relevant official/extension sources; retain label, safety, and location caveats and route uncertain cases to local extension support.

## Non-goals

- A guaranteed or prescriptive “best rotation” recommendation.
- Autonomous creation of a crop plan, operational task, disease problem, or treatment action without the appropriate farmer confirmation flow.
- Invented irrigation amounts, harvest dates, pesticide products, doses, or chemical mixing instructions.
- A single opaque weighted score combining unlike datasets.
- Claims of measured soil-health improvement without relevant measurements and evidence.
- Treating village names, upazila data, or regional grids as field-level observations.
- Querying/scraping external sources on every farmer request.
- Bulk mirroring government sites or redistributing material without checking reuse terms.
- Letting generated summaries create agronomic facts absent from reviewed source records.

## Approaches considered

1. **Citation-only links:** quickest, but leaves farmers to interpret source material and provides little structured evidence for comparison.
2. **Reviewed local evidence catalog (selected):** controlled collection from official sources, structured facts with provenance and human review, and separate NASA evidence inputs. Gives the app usable, auditable evidence without treating raw scraped content as authoritative.
3. **Live multi-source aggregator:** potentially fresher but brittle across APIs, page layouts, credentials, and service availability; unsuitable as the only path for a farmer comparison.

The selected design uses a reviewed catalog for agronomy knowledge, while source-appropriate NASA retrieval/cache may supply environmental observations. Collection is a controlled backend/manual process, not a request-time scrape.

## Source roles and trust boundaries

| Source family | Evidence role | Scope and display rule |
|---|---|---|
| BARC Crop Zoning / CZIS | Regional crop suitability, cropping patterns, soil fertility and economic context where published | The portal describes upazila-level assessment and a 1:50,000 land/soil database. Do not label as a farm soil test or guarantee. |
| BRRI and other Bangladesh research institutes | Crop varieties, crop sequences, calendars, management conditions, and research-backed mechanisms | Preserve geography, season, variety, publication/revision date, and stated conditions. |
| BAMIS / DAE | Dated district or national weather and agrometeorological advisories, crop-weather calendars | Show valid/issue period and issuing body. Never use a stale bulletin as current guidance or as climate history. |
| SRDI | Candidate soil/resource maps or reports, only after exact product coverage, scale, date, and reuse terms are checked | Keep mapped regional soil properties separate from farmer-entered or lab-measured field values. |
| NASA POWER and other selected NASA products | Historical or current Earth-observation/climate context for a specific comparison question | Preserve product/version, parameter, units, time range, scale, point/area method, retrieval time and cache status. Do not blend unlike products into an unexplained score. |

Prefer official APIs, published downloads, and documents. Use public-page HTML extraction only when a stable official access method is unavailable. Do not bypass access controls or retain/distribute content against its terms. Extract only decision-relevant fields and citations; retain original snapshots only when permitted and necessary for audit. Each extracted fact must retain URL, title, provider, retrieval date, source date/version, geography, units, extraction method, review status, and reuse/license notes.

Human review is required before extracted agronomy facts affect option applicability. Conflicting sources remain visible with their location/date/scope; prefer a newer and more geographically relevant source only when its authority and scope support that choice. Otherwise mark the comparison uncertain and direct the farmer to local extension advice.

## Farmer experience

1. **Account and fields:** Farmer creates an account and adds one or more fields. Each field can store administrative location, optional pin, area, land type, irrigation/resources, farmer-entered soil information, and a provenance label for each input.
2. **Crop history and priorities:** Farmer records current/previous crops and seasons, and can state goals or constraints. The app distinguishes observed/completed history from planned crops.
3. **Crop and rotation choice:** Crop Advisor compares locally documented options using farm profile, crop/season conditions, rotation history, farmer priorities, and relevant NASA climate evidence. Unknown details remain unknown. Comparison itself does not change a season.
4. **Confirmed season plan:** Farmer reviews and confirms a crop/variety/season plan. The owning planning module records the active season and creates the initial task schedule through existing module contracts; no silent operational writes.
5. **In-season support:** The app uses active crop, planting date, growth stage, local crop calendar, and available weather context to present due/upcoming tasks, irrigation/care guidance, risk notices, and a harvest window when evidence supports them. It shows the source and assumptions and avoids false precision.
6. **Disease/problem support:** Farmer may submit a crop photo. Disease analysis checks the active crop, reports a possible result and uncertainty, and recommends a safe next step. Only eligible confirmed results enter the farm problem workflow; uncertain results do not create treatment instructions. The disease result and any linked farm problem remain traceable.
7. **Treatment information:** If a reviewed official/extension source has applicable guidance, show it with crop/problem scope, source date, label/safety conditions, and link. Otherwise ask the farmer to consult local extension staff rather than inventing a product or dose.
8. **Chat and voice:** Bangla chat/voice can explain current field state, evidence, tasks, weather, or disease results. It retrieves and narrates module-owned facts; deterministic services and reviewed sources own computations and recommendations.
9. **Offline and saved results:** Show cached information with its retrieval date and staleness. Save comparisons only when requested; keep them private to the farmer and authorized collaborators. No stale advisory is presented as current.

Farmer-facing screens use plain Bangla and English, readable mobile layout, no unexplained acronyms, units beside values, status text not color alone, short next steps, and expandable evidence details.

Accessibility requirements: plain language, readable mobile layout, no unexplained acronym, units shown with values, distinct status text (not color alone), and a short actionable next step. Technical metadata remains available in an expandable evidence area.

## Evidence/status model

Use evidence statuses such as `good_coverage`, `partial_coverage`, `insufficient_data`, and `stale`; these describe data coverage, not calibrated probability or certainty about a farm. Each evidence claim is source-linked and typed as farmer-provided, NASA observation, regional agronomy, dated advisory, model output, or completed farm record. Source disagreement is shown as disagreement, not averaged away. Future projections carry separate model/scenario/period metadata and never masquerade as observations. Treatment guidance additionally records the exact source passage/version, applicable crop/problem, safety/label limitations, and review status.

## Constraints and open implementation choices

- Preserve existing M1 farm/profile ownership, M2 crop and rotation advisory, M3 active season/tasks/problems, M4 NASA and weather acquisition, M5 chat/voice explanation, and M6 disease analysis boundaries. Do not create a second farm store or move source computation into an LLM.
- Reuse existing data contracts only where field meaning matches. Any additive schema/API changes require migration and compatibility review.
- No user-provided Earthdata bearer token is required for NASA POWER. Any credentials for another source must remain server-side, outside code, logs, and browser bundles.
- Exact government data products/endpoints, licensing/reuse terms, update schedules, complete nationwide coverage, treatment-label applicability, and stable access methods must be verified before implementation. Website descriptions alone do not prove a downloadable dataset is available.
- Existing implementation is a partial foundation, not proof that the complete lifecycle works. Audit each current API and UI path before extending it; disease-model deployment weights and end-to-end test runtimes require separate verification.
- The current Desktop checkout is read-only in this environment; this proposed document is saved in the writable `Documents/ChatGPT/Fieldshift` workspace. Port it into the target checkout only when write access is available.

## Primary references reviewed

- NASA Field Shift challenge: https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/
- NASA challenge video: https://www.youtube.com/watch?v=cF0U2WXsM7o
- NASA POWER daily API: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- BARC Crop Zoning portal: https://portal.cropzoning.gov.bd/
- BARC Crop Zoning dashboard: https://dashboard.cropzoning.gov.bd/
- BAMIS overview: https://www.bamis.gov.bd/en/page/about-bamis-portal/
- BAMIS portal: https://www.bamis.gov.bd/
- BRRI farming systems/cropping-pattern information: https://brri.gov.bd/pages/static-pages/6922dec1933eb65569e1d1fc

The Claude artifact and the user's organizer build guide are planning references, not official NASA requirements. Their suggested datasets are candidates; a source is included only when its role, access, coverage, and limitations are verified.
