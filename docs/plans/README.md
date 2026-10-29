# FieldShift BD — সম্পূর্ণ updated plan

**আপডেট:** ২৯ অক্টোবর ২০২৬। এই index থেকে পুরো plan পড়া যাবে। Organizer-এর পাঁচটি নির্দেশনার image, final problem statement, বর্তমান M1–M6 foundation, Bangla voice/mobile delivery এবং owner-accepted তিনটি adaptive feature একসঙ্গে এই plan set-এর scope। এখানে বর্ণিত নতুন feature-গুলো planned; documentation update-কে implementation বা test success বলা হচ্ছে না।

## কোন document কী নির্ধারণ করে

| Document | বিষয় |
|---|---|
| [Canonical project plan](../../plan.md) | ছয় module-এর ownership, shared foundation, change control এবং Section 20-এর required outcomes |
| [NASA planting-window, rotation ও mobile delivery](2026-10-29-nasa-planting-window-and-rotation.md) | Organizer ও final statement-এর পূর্ণ scope, dataset/cache, onset/GDD/statistics, তিন rotation, interfaces, mobile/deployment এবং V01–V15 gates; §13-এ requirement traceability |
| [Adaptive decisions ও confirmed Plan B](2026-10-29-adaptive-decisions-and-confirmed-plan-b.md) | Decision-driven field question, robustness envelope, versioned contingency; proposed schema, atomic confirmation/retry, D0–D6 increments ও A01–A08 gates |
| [Bangla voice implementation](2026-10-06-voice-first-bangla.md) | Device speech/tap fallback, consent, confirmation, offline, F1–F9 user flow এবং CCR-1–CCR-12 |
| [Backend module skeleton](../../backend/contracts/README.md) | Existing M1–M6 route/model ownership, schema-checked seams, validated synthetic mocks and executable OpenAPI ownership check |

Engineering detail English-এ রাখা হয়েছে যাতে existing code/contracts-এর সঙ্গে মিল থাকে; Bangla farmer-facing text/voice-এর acceptance ওই document-গুলোতে নির্ধারিত। Root plan ownership নির্ধারণ করে; challenge plan science/scope, adaptive plan নতুন decision logic এবং voice plan accessibility নির্ধারণ করে। কোনো code contract ভিন্ন হলে implementer-কে additive diff নথিভুক্ত করতে হবে; ownership বদলানো যাবে না।

## Farmer-এর সম্পূর্ণ অভিজ্ঞতা

Password দিয়ে sign-in → সব saved farm দেখা → একটি farm বাছাই করে তার chat/advisory খোলা → saved location/resources/current rotation যাচাই → NASA evidence-সহ planting/transplanting window ও current rotation-এর সঙ্গে দুইটি alternative তুলনা → প্রয়োজন হলে সিদ্ধান্তে প্রভাব ফেলে এমন একটি field question → উত্তর read-back করে আলাদা confirmation-এ M1-তে save → নতুন authoritative result ও তার tested feasibility range দেখা → plan নির্বাচন/activation নিশ্চিত করা → M3-তে প্রয়োজনীয় tasks/state।

পরবর্তী dated observation-এ নির্বাচিত plan আর fit না করলে versioned contingency আবার হিসাব হবে। Source-supported বিকল্প থাকলে exact plan/task difference দেখানো হবে; farmer confirmation-এর পরে এক transaction-এ অনুমোদিত পরিবর্তন save হবে। একই request retry-তে ফল একবারই কার্যকর হবে। বপনের বাস্তব ইতিহাস, completed কাজ বা অন্য farm-এর state বদলে দেওয়া যাবে না। Chat, task list ও spoken reply একই committed result দেখাবে।

## Required scope

- সব ৬৪ Bangladesh district, অন্তত তিনটি source-supported crop/season profile এবং current rotation-সহ অন্তত তিনটি rotation strategy। Aman-কে আলাদা duplicate crop species না বানিয়ে Rice-এর season/variety context রাখতে হবে।
- ২০০১–২০২৫ historical baseline; ২০০১–২০১২ বনাম ২০১৩–২০২৫ onset distribution, source-backed GDD, Mann–Whitney comparison, uncertainty এবং ১৫/২০/২৫ mm sensitivity। Demo-র “১১ দিন” hardcode করা যাবে না।
- NASA POWER, IMERG, SMAP, MODIS NDVI এবং challenge plan-এ নির্ধারিত অন্যান্য NASA/local source family-র bounded role, QA, actual coverage ও provenance। SMAP-এর অনুপস্থিত পুরোনো বছর বা field-scale measurement বানানো যাবে না।
- District Parquet ও versioned manifest; `OFFLINE=1`-এ cache-only analysis। Disconnected phone-এর পুরোনো result ও queued write আলাদা করে দেখাতে হবে।
- Bangla/English actionable sentence, district map, distribution/GDD chart, rotation timeline, visible assumptions ও under-160-character share/SMS summary। Summary ছোট মানেই একটি Bangla SMS segment—এমন দাবি করা যাবে না।
- M1 profile/resources, M2 rules/plan definitions, M3 tasks/problems/current stage, M4 evidence, M5 chat/confirmation ও M6 disease lifecycle-এর existing ownership এবং compatibility বজায় রাখতে হবে।
- Accepted additions: একটি decision-changing observable question; bounded robustness range ও binding constraint; dated evidence-এ conditional Plan B এবং verified atomic confirmation। এগুলোর core logic-এ paid AI API লাগবে না।
- Real browser/mobile verification, physical Android install/voice/offline testing, source/license compliance, secure deployment, usable public repo, official project page ও recorded demo।

## কাজের ক্রম ও completion evidence

| ধাপ | কাজ | শেষ হওয়ার প্রমাণ |
|---|---|---|
| ১. Foundation | Existing M1–M6 baseline যাচাই; approved calendars/stages/tasks-এর gap পূরণ; contracts, source licensing ও release prerequisites | Clean DB lifecycle, evidence register, compatibility baseline; unresolved gap তালিকাভুক্ত |
| ২. Organizer science | Pinned cache, onset/GDD, distributions/statistics/sensitivity এবং `/advisory` | Parent V01–V06; হাতে হিসাবযোগ্য fixture ও source-backed actual result |
| ৩. Required farmer flow | Three rotations, farmer resources/priorities, map/chart, Bangla/English/tap/voice, offline ও confirmed season/task handoff | Parent V07–V13; browser ও physical Android observations |
| ৪. Adaptive decisions | Contract/schema diff → A01 question → A02 envelope → A03 policy preview → transactional confirmed execution | Adaptive D1–D5, A01–A08; PostgreSQL concurrency/rollback/retry, actual UI flow |
| ৫. Release/submission | Bounded refresh/delivery job, measured capacity, HTTPS/release build, recovery, licenses ও submission | Parent V14–V15 + adaptive D6; actual deploy/device/submission evidence |

Organizer-এর pre-build ও 48-hour schedule মূল challenge plan §11-এ আগের মতো আছে: Day 1 morning compute/tests, afternoon map/distributions, evening advisory ও 18:30 recording; Day 2 morning bilingual phone UI/outside-team test, noon freeze/submit। এটি initial milestone; সম্পূর্ণ scope 48 ঘণ্টায় শেষ হবে এমন প্রতিশ্রুতি নয়। Original cut order স্বয়ংক্রিয় scope waiver নয়। সব required gate pass না করলে full completion বলা যাবে না।

## নতুন তিন feature-এর স্পষ্ট সীমা

**Question:** কৃষক পর্যবেক্ষণ করে উত্তর দিতে পারেন এমন প্রশ্ন হবে; lab result আন্দাজ করতে বলা যাবে না। “জানি না”/skip থাকবে। Hypothetical answer farm profile-এ নিজে থেকে save হবে না।

**Robustness:** ঘোষিত scenario domain-এর calendar/resource feasibility দেখাবে। Non-monotonic বা আলাদা feasible range থাকলে তা রাখতে হবে; yield/survival guarantee নয়। Data না থাকলে axis unavailable থাকবে।

**Plan B:** stale evidence, বদলে যাওয়া plan/task/profile বা expired proposal-এর পুরোনো confirmation দিয়ে execution হবে না। আগে থেকে planted crop বদলাতে valid separately confirmed lifecycle transition প্রয়োজন; history rewrite চলবে না। One-time receipt, full rollback ও post-commit notification recovery নির্দিষ্ট করা হয়েছে।

Multi-farm rice-floor optimization, shared-pump scheduling, general minimal-change optimizer এবং outcome-study tooling এই তিন-feature approval-এর অন্তর্ভুক্ত নয়; research suggestion হিসেবেই রয়েছে।

## Supporting evidence

- [Organizer brief](references/2026-10-29-organizer/01-brief.png), [48-hour schedule](references/2026-10-29-organizer/02-48-hour-plan.png), [data guidance](references/2026-10-29-organizer/03-data.png), [architecture](references/2026-10-29-organizer/04-architecture.png), [build prompt](references/2026-10-29-organizer/05-build-prompt.png) ও [unedited final problem statement](references/2026-10-29-organizer/problem-statement.md)।
- [Current-code readiness review](../research/2026-10-28-challenge-readiness-review.md) ও [free mobile/voice feasibility](../research/2026-10-28-free-mobile-voice-feasibility.md)।
- [Competitor review ও recommendation—Bangla](../research/2026-10-29-competitor-feature-response-bn.md), [detailed opportunity analysis](../research/2026-10-29-competitor-feature-opportunities.md) ও [repository findings](../research/2026-10-29-competitor-repositories.md)।

Research report-গুলো review-এর সময়কার findings হিসেবে রাখা হয়েছে। কোন suggestion এখন accepted, তার authority হলো এই plan set-এর dated adaptive amendment; সব research suggestion স্বয়ংক্রিয়ভাবে scope নয়। Source-backed deterministic reasoning-এর জন্য paid API দরকার নেই, তবে free tools ব্যবহার করলেই indefinite production hosting/device/distribution খরচ শূন্য হবে—এমন নিশ্চয়তা দেওয়া হয়নি।
