# FieldShift BD: Competitor review ও feature recommendation

**পর্যালোচনার তারিখ:** ২৯ অক্টোবর ২০২৬
**পরিধি:** ব্যবহারকারীর দেওয়া দুইটি live demo, সম্পর্কিত NASA Space Apps repositories এবং FieldShift BD-এর বর্তমান code ও অনুমোদিত project plan-এর সঙ্গে তুলনা। এটি একটি সীমিত public-sample review—বিশ্বের সব প্রকল্পে কোনো feature নেই, এমন দাবি নয়।

## সংক্ষিপ্ত উত্তর

FieldShift BD-কে আলাদা করে তুলতে আরও একটি map, chatbot, ভাষা বা NASA data layer যোগ করাই যথেষ্ট হবে না। পর্যালোচিত প্রতিযোগীদের মধ্যে rotation ranking, historical replay, climate scenario, printable report, voice/offline interface এবং NASA map-এর উদাহরণ আছে। আমাদের full plan-এও planting-window analysis, GDD, rotation comparison, Bangla/English voice, provenance ও offline handling ইতিমধ্যে আছে—এসবকে নতুন আবিষ্কার হিসেবে দেখানো ঠিক হবে না।

সবচেয়ে শক্তিশালী অতিরিক্ত অভিজ্ঞতা হতে পারে:

> **অ্যাপ বুঝবে কোন অনুপস্থিত তথ্যের কারণে সিদ্ধান্ত বদলাতে পারে, কৃষককে সেই বিষয়ে একটি কাজে লাগার মতো প্রশ্ন করবে, পরিকল্পনাটি কতদূর পর্যন্ত feasible তা দেখাবে, আর শর্ত বদলালে বিকল্প পরিকল্পনা প্রস্তাব করে কৃষকের অনুমোদন নেবে।**

এটি M1-এর farm তথ্য, M2-এর advisor, M4-এর dated environmental evidence, M5-এর Bangla ব্যাখ্যা এবং M3-এর task/update flow-কে একটি যাচাইযোগ্য সিদ্ধান্ত-থেকে-কাজের ধারায় যুক্ত করে। এটি জেতার নিশ্চয়তা নয়; বৈজ্ঞানিকভাবে সঠিক, বাস্তবে কাজ করা demo-ই মূল।

## প্রতিযোগীদের মধ্যে যা দেখা গেছে

| প্রকল্প | দেখা feature | কী সীমা মাথায় রাখা দরকার |
|---|---|---|
| [CropSafe live demo](https://cropsafe.neonweb.xyz/) / [repository](https://github.com/FahadIslam09/fieldshift) | Tanore sample-এ পরের crop-এর বিকল্প, planting calendar, pump/fuel estimate; standing crop-এর জন্য AWD ও heat-stage advice | পর্যালোচিত [calendar code](https://github.com/FahadIslam09/fieldshift/blob/649f3115aa37f0de6af051d61bb0f4166a1c4607/src/lib/calendar-optimizer.ts)-এ crop/zone অনুযায়ী fixed shift/configuration আছে; এটি ২৫ বছরের rainfall distribution থেকে shift গণনা করে না। [NASA POWER adapter](https://github.com/FahadIslam09/fieldshift/blob/649f3115aa37f0de6af051d61bb0f4166a1c4607/src/services/nasa-power.ts) live data আনে, তবে fallback telemetry-ও আছে। দেখানো saving/protection-কে field-validated ফল ধরে নেওয়া যাবে না। |
| [Samuel-এর FieldShift demo](https://samuelakosaonyejekwe.github.io/fieldshift/) / [repository](https://github.com/samuelakosaonyejekwe/fieldshift) | Historical replay, climate lens, rotation details, soil/water/income indicators, task calendar, report/share এবং offline-readiness view | [engine.js](https://github.com/samuelakosaonyejekwe/fieldshift/blob/8a8b8be0f603dde3e5c6312da9280eff55f38299/js/engine.js)-এ heuristic outcome/soil/economic calculation আছে। UI-তে দেখা ফল field validation প্রমাণ করে না; offline mode, language quality এবং export আলাদাভাবে যাচাই করা হয়নি। |
| [CropShift](https://github.com/Taaanha/Crop-Shift) | Analog year ও historical replay-এর ধারণা, data receipt | README-তে বর্ণিত; এই review-তে implementation ও engine স্বাধীনভাবে যাচাই করা যায়নি। |
| [RotaShift](https://github.com/XtremeseOISHEE/RotaShift) | “Adaptation Margin”—পরিকল্পনা কতদিন shift সহ্য করে, household priority | [Prototype source](https://raw.githubusercontent.com/XtremeseOISHEE/RotaShift/main/rotashift.html)-এ margin interaction আছে; README অনুযায়ী figure illustrative, validated farm outcome নয়। |
| [Sky2Root](https://github.com/spaul571/sky2root) | Season replay ও extension-agent view | [model.js](https://github.com/spaul571/sky2root/blob/main/prototype/js/model.js) seeded illustrative outcome তৈরি করে; real imagery/NDVI-কে modeled result থেকে আলাদা রাখতে হবে। |
| [Space Hunters / FIELD SHIFT](https://github.com/AhmedSalah-26/space-hunters) | Three-season matrix, presentation/export flow এবং POWER climatology | [DecisionMatrixScreen.jsx](https://github.com/AhmedSalah-26/space-hunters/blob/main/src/components/DecisionMatrixScreen.jsx)-এ কিছু score fixed heuristic increment-এ নির্ভরশীল; live POWER data থাকলেই সব score বৈজ্ঞানিকভাবে যাচাইকৃত হয় না। |
| [BoponX / Team EARTH.exe](https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026) | Evidence gate, printable plan এবং data availability ও recommendation authority আলাদা করে দেখানো | [agronomy.py](https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026/blob/main/backend/app/compute/agronomy.py)-তে BAMIS calendar উপস্থিতি suitability প্রমাণ বলে ধরা হয়নি—এটি সততার ভালো উদাহরণ। |
| [AgriGuard](https://github.com/ESR-style/AgriGuard) | Irrigation view ও river alert | পর্যালোচিত implementation-এ demonstration threshold আছে; সেগুলো Bangladesh-এর যাচাইকৃত threshold হিসেবে নেওয়া যাবে না। |
| [WaterWise / GaamaRamma](https://www.spaceappschallenge.org/nasa-space-apps-2024/find-a-team/gaamaramma/?tab=project) | ET/rainfall তথ্য থেকে ব্যবহারযোগ্য ৭ দিনের irrigation schedule | NASA-এর [২০২৪ সালের official results](https://www.nasa.gov/learning-resources/stem-engagement-at-nasa/nasa-international-space-apps-challenge-announces-2024-global-winners/) তাদের Best Use of Data award নিশ্চিত করে। তাদের OpenET-ভিত্তিক coverage বাংলাদেশে আছে ধরে নেওয়া যাবে না। |

দুইটি সরাসরি দেওয়া live site-ই পর্যালোচনা করা হয়েছে। অন্য project-এর ক্ষেত্রে public README/source-এ যা পাওয়া গেছে, তার বাইরে capability বা ফলাফল ধরে নেওয়া হয়নি।

## যে feature-গুলো যোগ করলে সবচেয়ে বেশি পার্থক্য হতে পারে

### ১. সিদ্ধান্ত বদলায় এমন একটি field question

কোনো অজানা তথ্য—যেমন সেচ সময়মতো পাওয়া যায় কি না বা জমিতে পানি জমে থাকে কি না—কোন crop/rotation feasible হবে তা বদলালে, অ্যাপ একটি নিরাপদ ও পর্যবেক্ষণযোগ্য প্রশ্ন করবে। উত্তর না থাকলে একটিমাত্র নিশ্চিত recommendation দেওয়ার ভান না করে বলবে কোন বিকল্পগুলো এখনও সম্ভব। Lab test দরকার এমন তথ্য কৃষককে আন্দাজ করতে বলা যাবে না। Satellite moisture আর কৃষকের মাঠের পর্যবেক্ষণ আলাদা হলে তারিখ ও মাপের পরিসরসহ দুটোই দেখাতে হবে; অন্ধভাবে গড় করা যাবে না।

এটি M1-এর progressive farm intake, M2-এর deterministic feasibility/sensitivity check এবং M5-এর সংক্ষিপ্ত Bangla প্রশ্নের সঙ্গে মানায়। Transparent rule-based logic যথেষ্ট—এখানে paid AI বা calibrated Bayesian probability দাবি করার প্রয়োজন নেই।

**যাচাই:** প্রশ্নটির উত্তর সত্যিই feasible option বা ranking বদলায় কি না; অপ্রাসঙ্গিক প্রশ্ন বাদ পড়ে কি না; অজানা তথ্য অজানাই থাকে কি না।

### ২. Rotation robustness margin ও বাধা হয়ে থাকা constraint

“এই plan কতদিন delay, কতটা water constraint, বা কোন heat condition পর্যন্ত calendar/resource rule মেনে চলে?”—তার একটি bounded range দেখানো। কোন crop/stage-এ plan আর feasible থাকে না, সেটি এবং কোন তথ্য দিয়ে হিসাব হয়েছে তা খুলে দেখা যাবে। একক “safe percentage” দেখানো হবে না।

RotaShift-এ sample Adaptation Margin আগে থেকেই আছে। তাই ধারণাটিকে নতুন আবিষ্কার বলা যাবে না; FieldShift BD-র পার্থক্য হতে পারে বাস্তব local calendar/data দিয়ে reproducible হিসাব, uncertainty এবং পরের action-এর সঙ্গে সংযোগ। এটি yield বা crop survival-এর নিশ্চয়তা নয়। Feasibility non-monotonic হলে ভুল binary search না করে পুরো নির্ধারিত scenario range যাচাই করতে হবে।

**যাচাই:** হাতে হিসাব করা feasible/infeasible boundary, একাধিক feasible range, crop overlap ও missing-data case।

### ৩. শর্তসাপেক্ষ Plan B, কৃষকের অনুমোদনসহ

প্রতিটি নির্বাচিত rotation-এর সঙ্গে versioned contingency রাখা: কোন dated observation এলে আবার হিসাব হবে, latest feasible date কী, বিকল্পটি কোন evidence-এ সমর্থিত, এবং কোন পরিবর্তনে কৃষকের নতুন সম্মতি লাগবে। শর্ত পূরণ হলে অ্যাপ সুনির্দিষ্ট কারণসহ পরিবর্তিত calendar/task প্রস্তাব করবে; নিজে থেকে crop switch বা duplicate task তৈরি করবে না। Forecast-কে observed event বলা যাবে না, আর stale cache দিয়ে নতুন trigger চালানো যাবে না।

এটি M4-এর evidence → M2-এর recalculation → M5-এর confirmation → M3-এর idempotent task/update flow যুক্ত করে। বর্তমান plan-এ alerts/confirmation আছে, কিন্তু প্রতি rotation-এর জন্য explicit saved contingency policy একটি বাড়তি আচরণ।

**যাচাই:** একই confirmation পুনরায় পাঠালে duplicate update না হওয়া, expired/contradictory evidence-এ trigger না হওয়া এবং completed task নীরবে overwrite না হওয়া।

### বাড়তি সুযোগ—পরে বিবেচনা করা যায়

- **Multi-farm rice floor:** কৃষক নিজের ন্যূনতম rice area বা staple target ঠিক করে; একাধিক saved farm-এ বাকি crop allocation তুলনা হয়। নির্ভরযোগ্য yield data না থাকলে farmer-selected area floor ব্যবহার করতে হবে, food-security guarantee নয়।
- **নিজের farms জুড়ে shared pump schedule:** pump flow/capacity, availability, irrigation hours ও farm access দিয়ে overlapping demand যাচাই। Capacity না মিললে rotation feasible দেখানো যাবে না। একাধিক পরিবারের resource share করলে permission/privacy আলাদা করে লাগবে।
- **“আমার পছন্দের crop কেন নয়?”:** কোন binding constraint বাধা হচ্ছে এবং কোন locally supported date/variety/resource change-এ feasible হতে পারে তা দেখানো; অনুমানভিত্তিক খরচ বা borrowing advice নয়।
- **Recommendation থেকে observed season outcome:** ব্যবহৃত data/model version-এর সঙ্গে কৃষকের actual planting/harvest date ও failure reason যুক্ত করা। Observational data-কে causal proof বলা যাবে না।

## Judges-দের criteria-র সঙ্গে সংযোগ

- **Validity:** সঠিক onset/GDD/calendar, উৎসসহ threshold, uncertainty, missing-data-তে fail-closed behavior এবং hand-checkable test দেখাতে হবে। সুন্দর chart একা validity নয়।
- **Relevance:** NASA data যেন সিদ্ধান্তে বাস্তব ভূমিকা রাখে—কোন NASA observation কোন হিসাব বদলেছে তা traceable হোক; decorative layer হিসেবে না থাকে।
- **Presentation:** একটি নির্দিষ্ট কৃষকের সিদ্ধান্তের গল্প দেখান: একটি প্রশ্ন → বদলানো feasible option → margin/constraint → farmer-confirmed Plan B।
- **User experience:** Bangla-তে ফোনে, দলের বাইরের কৃষক/ব্যবহারকারী দিয়ে task completion ও বোঝাপড়া যাচাই করুন। শুধু browser screenshot যথেষ্ট নয়।
- **NASA data usage:** NASA POWER, IMERG, SMAP বা NDVI-র মতো source-এর বাস্তব ব্যবহার, dataset date/coverage, citation ও সীমাবদ্ধতা UI-তে স্পষ্ট করুন। NASA badge বা endorsement দাবি করবেন না।

এগুলো supplied judging image-এর criteria-র সঙ্গে আমাদের feature mapping; score বা জয়ের পূর্বাভাস নয়।

## সবচেয়ে জোরালো demo-র ধারাবাহিকতা

1. একটি বাস্তব supported district/farm ও evidence-backed rotation তুলনা দেখান।
2. সেচ-সংক্রান্ত তথ্য অনিশ্চিত রাখুন; অ্যাপ দেখাক কেন এতে সিদ্ধান্ত বদলায় এবং একটি সহজ প্রশ্ন করুক।
3. নিশ্চিত উত্তর দিলে feasible option ও তার কারণ বদলাক।
4. কোন সীমা পেরোলে plan আর fit করবে না, এবং কোন supported alternative আছে, দেখান।
5. নতুন dated observation/scenario এলে সুনির্দিষ্ট task diff প্রস্তাব করুন; farmer confirmation-এর পর একবারই M3-তে update হোক।
6. উৎস, data age, uncertainty এবং unsupported-case fallback দেখান।

৩D globe, আরও ভাষা, আরেকটি chatbot, certificate badge বা উৎসহীন water-saving percentage-কে প্রধান novelty না করাই ভালো। Full project plan-এ আগে থেকেই থাকা onset/GDD, rotation, voice, offline, map ও provenance-কে “নতুন feature” বলে দেখাবেন না।

## গবেষণার বিস্তারিত ও source সীমা

- [Competitor repository review](2026-10-29-competitor-repositories.md) — source-level findings, commit snapshots ও প্রতিটি project-এর সীমাবদ্ধতা।
- [Feature opportunity analysis](2026-10-29-competitor-feature-opportunities.md) — ranked additions, implementation fit, proof criteria ও demo suggestion।
- [NASA planting-window and rotation plan](../plans/2026-10-29-nasa-planting-window-and-rotation.md) — এই review-তে “আগেই planned” বলা feature-গুলোর পূর্ণ scope।

কোনো competitor code, image বা data reuse করার আগে প্রকৃত license ও attribution যাচাই করতে হবে। এই review-তে competitor code কপি করা হয়নি।
