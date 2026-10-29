# Voice-First Bangla Experience — Implementation Plan

> **Revised 2026-10-29:** This is the voice/accessibility delivery plan for [the organizer and final-challenge implementation plan](2026-10-29-nasa-planting-window-and-rotation.md), under `plan.md` Section 20. All five organizer images and the complete final statement are preserved and mapped there. Voice delivers the planting-window and rotation decisions; it does not substitute for their scientific implementation. Checkboxes are targets, not claims of completed work.
>
> **For contributors:** Use the existing Expo/FastAPI app and module contracts. Track implementation and verification evidence for each phase, the parent plan's V01-V15 gates and the accepted adaptive-decision A01-A08 gates. Read the [complete plan index](README.md) and [adaptive-decision specification](2026-10-29-adaptive-decisions-and-confirmed-plan-b.md). F9/CCR-12 below integrate the owner's accepted three-feature follow-up.

**Goal:** Let a Bangladeshi farmer with limited literacy and little smartphone experience explore NASA-informed planting/transplanting windows and at least three rotation strategies, understand evidence/tradeoffs, and use the season-long assistant mainly by speaking Bangla and listening. Every voice action has a tap path. Bangla and English expose the same computed facts.

**Architecture:** Voice is an input/output channel of the one assistant, not a seventh module. Tier 0 recognition, playback and confirmation UI live on the device; optional server STT/TTS and backend action orchestration belong to M5. M4 supplies environmental evidence, M2 owns planting/rotation science, M1 owns profiles, M3 owns operational tasks/problems and M6 owns disease analysis. Voice does not acquire their data ownership.

**Tech Stack:** Existing Expo SDK 57 / React Native 0.86 / Expo Router, FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL, Docker Compose (dev). Reuse image picker, location, API client and SecureStore. Add device speech/audio/localization/cache facilities after compatibility checks. Server STT/TTS is an optional later adapter; no paid model/API is needed for deterministic advisory or basic voice.

**Cost strategy:** Build an Android pilot without purchased voice APIs using device engines and recorded prompts. Existing hardware/free quotas can cover a bounded pilot; they do not guarantee indefinitely free, durable production. See §4.0 and the [feasibility review](../research/2026-10-28-free-mobile-voice-feasibility.md).

## 0. Required Challenge Integration and Delivery Order

1. Follow the parent plan's complete requirement matrix: 2001-2025 onset/GDD, 2001-2012 versus 2013-2025 distributions, Mann-Whitney U, supported whole-day window shift and ±5 mm sensitivity; NASA/local data, map/charts, assumptions/provenance; three rotations, soil/resources and farmer priorities.
2. Compute/cache the science before narrating it. `/advisory?district=&crop=` and authenticated M2 farm scenarios supply every displayed/spoken date, shift, uncertainty and evidence ID. An LLM cannot invent or recalculate them.
3. First voice slice: select district/crop or farm, hear/replay the actionable Bangla advisory, ask why, compare rotations and hear today's tasks. Structured writes follow owner-contract integration. Core UI remains bilingual and tap accessible.
4. Show onset definition and every assumption, with spoken explanations. Generate SMS summaries strictly below 160 Unicode characters from the typed result; show true Bangla SMS segment implications rather than promising one segment.
5. Preserve sign-in → all saved farms → selected farm chat. Never silently select a farm from a district voice command or replace the entry flow with a private spoken summary.
6. Chrome validates layout; physical Android release/development builds validate speech, permissions, mic lifecycle, installed Bengali models/voices, offline behavior and low-memory usability.
7. Follow the parent's pre-event/48-hour milestone and full release gates. The organizer's cut order is a separately authorized contingency, not permission to omit full requirements silently.

## Global Constraints

- `plan.md` is the source of truth. Do not move features between modules or change shared contracts without team agreement (plan.md §10 Rules A–C, §19). Every contract change in this plan is listed in **§9 Contract Change Requests** and is **blocked until the team agrees**.
- The app must **not** listen while closed or in the background. Microphone opens only after a user action (tap, widget tap, shortcut, or assistant "open app" launch) while the app is visible.
- **No voice-commanded farm save, update, delete, or external send without explicit confirmation** (§6). Explain ordinary transcript/chat persistence and analytical caching through consent; technical logs do not recursively ask permission for every write.
- Every voice action has a tap alternative. Every text label has an icon and a "hear this" option.
- Bangla (`bn-BD`) is the default UI and speech language. English is secondary.
- Audio is **not retained** by default. Audio retention needs separate, opt-in consent.
- Store files outside PostgreSQL; keep only a storage key (DB_SCHEMA.md §1, §10).
- Frontend: use `npx expo install` for packages; native modules need a development build (not Expo Go). Run `npx expo lint` and `npx tsc --noEmit` before done (frontend/AGENTS.md). Verify every Expo API against SDK 57 docs before use.
- Do not edit `ios/` or `android/` by hand; use `app.json` and config plugins (frontend/AGENTS.md).
- **Pilot cost constraint:** no purchased speech/LLM/SMS API is required. Hosting, persistent storage, licenses and distribution must pass the parent gates; do not promise indefinite zero operating cost.
- **License rule:** use only models/datasets that allow commercial use (MIT, Apache-2.0, CC-BY, CC-BY-SA with attribution). **Do not use non-commercial (NC) models**, e.g. Meta MMS-TTS / MMS-ASR (CC-BY-NC 4.0). Check the license of every fine-tuned checkpoint before use.

---

## 1. Current State of the Repository (reconciled 2026-10-29)

Baseline source inspection: `1077a06`; this inventory is not a new runtime-test result.

| Area | Existing implementation / remaining gap |
|---|---|
| Auth/profile | M1 password auth, Argon2id, farm listing/location/resources and token storage exist; reuse them |
| Frontend/backend | M1-M6 services, screens, chat replies, image picker/upload and tests exist; do not rebuild placeholders |
| M2 knowledge | Narrow suitability/harvest evidence exists; verified season stages/tasks still need sourcing for clean-user plan activation |
| NASA | Current POWER history is 30 days; district caches, long-history onset/GDD/statistics, projections and rotations remain parent work |
| Voice/localization | Device speech, Bangla UI/audio, consent/preferences and structured action confirmation remain work |
| Offline/release | Secure token storage exists; account-isolated farm/result caches/outbox, real release identity/API URL, native testing and durable hosting remain work |
| M6 conflict | Current scan auto-creates/reuses an M3 Problem for possible disease; a later UI confirm cannot prevent that write. Reconcile with owners before F6 |

Reuse existing auth, routes, models and fixtures. Add missing source-backed data/interfaces rather than competing systems. Add Bangla/voice scenarios without using synthetic test agronomy as production advice. See the [source review](../research/2026-10-28-challenge-readiness-review.md) and parent §3 for evidence paths.

---

## 2. Design Principles for Low-Literacy, First-Time Smartphone Users

1. **One big mic button** on every screen, bottom center, same place always. Tap to talk, tap again to stop (hold-to-talk is hard for new users; offer it as a setting).
2. **Talk back first, text second.** Every assistant reply plays as audio automatically (can turn off). Text is shown large, in Bangla, with a replay button.
3. **Short replies.** First reply ≤ 2 short sentences. Then: "আরও শুনতে চাইলে 'আরও' বলুন" + a "আরও" button.
4. **Icons + color + sound on every control.** Long-press any button → it speaks its name. Max 4 main choices per screen.
5. **Farm summary = "আজকে কী করবো".** After explicit farm selection, offer today's task/alert and planting/rotation advice. Sign-in still opens all farms; no private summary for an implicitly selected farm.
6. **Never a dead end.** Every screen has "পেছনে" (back) and "শুরুতে" (home), both by voice and tap.
7. **Yes/No is the main decision pattern.** Big green ✓ "হ্যাঁ" and red ✗ "না" buttons; the farmer can also say them.
8. **Numbers spoken the farmer's way:** "দেড় বিঘা", "আড়াই মণ", "৩০ শতাংশ", "পরশু".
9. **Shared phones are common** (assumption A4): show the active farmer's name + photo; switching user is a voice/tap action.

---

## 3. Opening the App by Voice — Platform Assessment

### 3.1 What the platforms allow

**Android**
- A third-party app **cannot** keep an always-on wake word. The always-on hotword APIs (`AlwaysOnHotwordDetector`, `HotwordDetectionService`) are system APIs for the privileged default assistant only (Android 12+).
- Microphone access is "while-in-use". A microphone foreground service cannot start from the background (Android 12+); on Android 14+ it throws `SecurityException`. Android 17 adds more background-audio limits.
- A home-screen widget tap, app shortcut, Quick Settings tile tap, or notification tap **is** a user action that brings the app to the foreground. The app may then open the mic.
- The default assistant (Google Assistant / Gemini) can open installed apps by name. Gemini supports Bengali and is available in Bangladesh. **Whether "open <app>" device actions work with Bengali voice is not documented** → test in Phase 0.

**iOS**
- No third-party wake word or background listening (App Review and platform limits).
- Siri has **no standalone Bangla**. It only accepts Bangla mixed with English in "English (India)" mode; replies are not in Bangla.
- Do not assume usable `bn-BD` recognition from `SFSpeechRecognizer`. Query actual OS/device capability and test recognized language; unsupported Bangla means tap-first. Never substitute another language silently or infer speech recognition from keyboard support.
- iOS does have Bengali (India) voices for VoiceOver / Live Speech → system TTS in Bangla is likely usable (verify).
- Launch options: App Intents / App Shortcuts ("Hey Siri, open FieldShift" in English), home/lock-screen widgets, Control Center controls (iOS 18+), Action Button (newer Pro models), Back Tap (accessibility).

### 3.2 Recommendation (practical and privacy-conscious)

**No custom wake word. No background listening.** Reasons: blocked by both platforms for third-party apps, high battery cost, Play Store foreground-service declarations, and it would break farmer trust (a hot mic in the pocket).

Instead, "one touch to talk":

| Priority | Entry point | Platform | Behavior |
|---|---|---|---|
| P1 | **Launcher icon with a Bangla, speakable name** (e.g. label "ফিল্ডশিফট") | Both | Opens auth/all-farms entry; after farm selection offers summary. Mic needs the intended user action. |
| P1 | **Home-screen widget: one big mic button** | Android first | Tap → deep link `fieldshift://listen` → app opens in listening mode immediately (user action = allowed). |
| P1 | **Notification tap on an alert/task** | Both | Opens the item and plays it aloud. |
| P2 | **App shortcuts** (long-press icon): "প্রশ্ন করুন", "আজকের কাজ", "ফসলের ছবি" | Both | Deep links to listen / tasks / camera. |
| P2 | **Default assistant "open FieldShift"** | Android (Gemini/Assistant), iOS (Siri, English) | Works only if the assistant supports it; test with Bengali settings. We do not rely on it. |
| P3 | Quick Settings tile (Android), Control Center control / Action Button (iOS) | Both | Same deep link. Lower priority: hard for first-time users to set up. |

Field agents / family members set up the widget during onboarding (assumption A6). The onboarding includes a spoken "how to open me" lesson.

---

## 4. Speech Stack

### 4.0 Cost Tiers

| Tier | When | STT | TTS | Platforms | Cost |
|---|---|---|---|---|---|
| **Tier 0 — No purchased speech API (v1)** | Prototype and bounded pilot | Android device recognition with verified `bn-BD`/`bn-IN` support, online/on-device as available | Bundled prompts and installed Bengali system TTS | Android first; iOS tap-first unless tested otherwise | No app speech API fee; device/data/hosting resources still exist |
| **Tier 1 — Self-hosted open source** | Measured need and provisioned hosting | Evaluate exact Whisper/IndicConformer checkpoints and upstream rights on local samples | Evaluate exact Indic Parler-TTS or other licensed checkpoint; measure RAM/latency | Android + iOS | CPU/GPU, storage and operations |
| **Tier 2 — Paid cloud** | Only if Tier 1 fails accuracy/latency targets | e.g. Google Cloud STT `bn-BD`, Gemini Live API `bn-BD` | Cloud TTS | Android + iOS | Per-minute fees |

Tier 0 consequences (accepted for v1):
- Accuracy depends on the phone's engine (usually Google). It cannot be fine-tuned for dialects. Mitigate with the command lexicon, read-back, and tap fallback.
- When online, the Android recognizer normally sends audio to the engine vendor (Google). Consent C2 must say this (§5).
- Supported locales differ by phone/OEM. Check at runtime; if `bn-BD`/`bn-IN` is absent → tap mode.
- iOS stays tap-first unless actual capability tests establish usable Bangla STT; use installed TTS/prompts where available.
- Free zero-cost tools for development only (not for serving users): own laptop, Google Colab/Kaggle free tiers for Tier 1 model evaluation.

### 4.1 Speech-to-text (STT)

Layered approach behind one interface (`SpeechRecognizer` on device, `SttProvider` on server). **v1 uses layers B and C only (Tier 0).** Layer A is added in Tier 1/2.

| Layer | Use | Engine | Notes |
|---|---|---|---|
| **A. Server STT (Tier 1/2)** | Free speech: questions, farm details, problem descriptions | Tier 1: `tugstugi` Whisper-medium or IndicConformer, self-hosted. Tier 2: Google Cloud STT `bn-BD`, Gemini Live API `bn-BD`. Chosen by bake-off on field data. | Works on iOS and Android. Needs network and hosting. Provider is swappable. |
| **B. Device STT (Tier 0 default)** | Supported Android speech | On Android 13+ query supported/downloaded locales and download where supported. Android 12 and below cannot use this library's `getSupportedLocales()`; use availability/attempt/error handling. Prefer verified on-device mode; disclose online mode or offer taps. | No speech API purchase; quality/availability varies. Never silently recognize another language. |
| **C. No STT** | Unsupported locale, offline without model, permission denied | Tap choices, prerecorded prompts/text; no automatic raw recording | Tap path remains available. |

Evaluate exact checkpoints on Bangla samples; a wrong-script anecdote is not a universal rejection of every small model. Do not bundle large speech models in low-end Android v1 without measured feasibility. Check original weights/data rights as well as converted-port labels.

**Command matching:** Normalize transcript (Bangla/English digits, remove filler words, collapse spelling variants) → match against a **command lexicon** with dialect synonyms (e.g. "কাজ / কাম / কামকাজ", "আজকে / আইজকা / আজ"). If no command match → send to M5 intent routing.

**Number/unit/date parser (Bangla):** "দেড়", "আড়াই", "সোয়া", "পৌনে"; units বিঘা, শতাংশ/শতক, কাঠা, একর, মণ, কেজি; dates "আজ", "কাল", "পরশু", "আগামী সোমবার", Bangla month names. Output always goes through read-back confirmation.

> **Bigha conflict:** DB_SCHEMA.md excludes `bigha` until a region-specific conversion is agreed. Farmers will say বিঘা. Proposal (CCR-5): store the spoken value + unit as said, ask the farmer "আপনার এলাকায় এক বিঘা কত শতাংশ?" once, then convert. Team decision needed.

### 4.2 Text-to-speech (TTS) and audio

| Content | Source | Why |
|---|---|---|
| Fixed prompts (menu names, onboarding, confirmations, errors, yes/no) | **Pre-recorded human Bangla voice**, bundled in the app (~150–250 clips, Opus) | Most natural, works offline, consistent, zero cost (team/volunteer voice with a signed release). Use a clear standard Bangla speaker; field-test understanding across dialects. |
| Dynamic text (answers, task titles, alerts) | **Tier 0:** device TTS (`expo-speech`, `bn-BD`/`bn-IN` voice). **Tier 1:** server TTS (`vits_rasa_13` / Indic Parler-TTS), cached by text hash | Android Google TTS has Bengali; iOS has Bengali (India) voices (verify quality). If the phone has no Bengali voice → show text + play the nearest bundled prompt. |
| Long answers | Tier 0: device TTS, split into short sentences. Tier 1: server TTS, cached | Consistent voice across devices only at Tier 1. |

Speech rate default 0.85–0.9× (tune in field). Replay button on every spoken message.

### 4.3 Local accents and dialects
- Phase 0 dataset: record consented samples from target regions (§11) and measure WER/CER per region and noise level per candidate engine.
- Dialect synonym lexicon for commands, crops (with M2 catalogue), units, and dates. Owned by M5 (commands) and M2 (crop names — read only).
- Allow the farmer to answer any question with a tap list; voice is never the only path.
- Optional later: contextual biasing / phrase hints (crop names, farmland names) if the chosen STT provider supports it.

### 4.4 Noisy environments
- Show a live level meter while listening; if noise is too high: "চারপাশে অনেক শব্দ। ফোন মুখের কাছে আনুন।"
- Voice activity detection (VAD) end-pointing + max clip length (15 s for commands/questions, 60 s for descriptions).
- Tier 1: server-side VAD and noise suppression before STT with open-source tools (Silero VAD — MIT, RNNoise — BSD). Tier 0: rely on the device engine; give the farmer coaching prompts instead.
- Support wired/Bluetooth headsets.
- Field test conditions: wind, irrigation pump/shallow tube-well engine, rain on tin roof, market crowd, livestock.

### 4.5 Weak or no internet
- **Offline-first queue**: eligible transcripts/messages, photos and confirmed actions show "পাঠানো হবে". Queue raw audio only if an implemented adapter provides recordings and consent/retention explicitly covers temporary storage. Device STT does not guarantee recoverable audio.
- Confirmed actions carry an **idempotency key** so retries never double-apply.
- Cache: today's tasks, alerts, farm summary, and their TTS audio, so Home works offline.
- Audio upload: Opus ~16 kbps mono 16 kHz; resumable/retry with backoff; timeouts sized for 2G/EDGE.
- Network-state indicator as an icon + sound, not text only.
- Scope queued data by farmer/farm/season/request ID/creation/expiry/state version. Reject stale/conflicting actions and clear/isolate data on logout/account switch; never replay old irrigation advice as today's instruction.
- Parent `OFFLINE=1` means cache-only server analysis, not disconnected-phone STT/geocoding/tiles. Bundle permitted compact map/results and show source age.

### 4.6 Unclear speech — handling rules
| Situation | Behavior |
|---|---|
| Silence / nothing heard | "কিছু শুনতে পাইনি। আবার বলুন।" + mic stays ready. |
| Low STT confidence, or no intent match | "আমি ঠিক বুঝিনি।" Then show/speak **top 2–3 guesses as big picture buttons**: "আপনি কি এটা বলতে চেয়েছেন?" |
| Second failure in a row | Switch to tap mode for this step: show the choices with icons; mic still available. |
| Ambiguous slot (e.g. which farmland, which task) | Ask one short question with tap choices: "কোন জমির কথা? উত্তরের জমি না দক্ষিণের জমি?" |
| Out-of-scope (e.g. loan, market price) | Say what the app can do; do not invent an answer (plan.md §16). |
| Transcript contains a number/date/unit | Always read back in words before any save. |

Confidence thresholds are provider-specific; calibrate in Phase 0 (assumption A8). Rule: **never guess for a write action.**

---

## 5. Consent and Privacy

1. **First-run consent, spoken + shown, in Bangla.** Separate, plain choices:
   - C1 Microphone use (required for voice; tap-only mode works without it).
   - C2 Voice is converted to text over the internet. **Tier 0:** by the phone's speech service (usually Google) — say so by name. **Tier 1/2:** by our server or our provider. Explain: "আপনার কথা লেখায় বদলাতে ইন্টারনেটে পাঠানো হয়". Re-ask C2 when the tier changes.
   - C3 Keep voice recordings to improve the app (**optional, off by default**).
   - C4 Camera/photos for crop problems (asked at first use).
   Consent is given by tapping "হ্যাঁ, রাজি". A spoken "হ্যাঁ" is recorded as supporting evidence but the tap is required for C2/C3 (assumption A9 — legal review).
2. OS permission prompt appears only after our own spoken explanation (pre-permission screen).
3. **Mic indicator:** clear "শুনছি…" animation + sound cue at start and stop. No listening without it.
4. **Retention:** audio deleted after transcription unless C3 = yes. Transcripts are kept as chat messages (needed for farm context). C3 recordings: retention limit (proposal 90 days) and delete-on-request.
5. **Withdraw anytime:** Settings → "আমার তথ্য" → voice/tap toggles; spoken command "আমার রেকর্ডিং মুছে দাও" → Tier 2 confirmation.
6. Consent records are versioned (text version, time, method, device). Owner: M1 (farmer data) — **CCR-2**.
7. STT/TTS provider: Tier 0 — follow the device engine's terms and disclose them. Tier 1 — audio stays on our server. Tier 2 — data processing agreement, no training on our audio unless C3, region/transfer reviewed. Check current Bangladesh personal-data law before launch (assumption A10).
8. Never put personal data in URLs or logs; redact phone numbers in transcripts sent to analytics.

---

## 6. Confirmation Policy (applies to all flows)

| Tier | Action examples | Confirmation |
|---|---|---|
| **T0 Read / navigate** | Open tasks, hear alerts, ask a question, go back | None. Announce what happened ("আজকের কাজ খুললাম"). Undo = "পেছনে". |
| **T1 Save / change own data** | Mark task done/skipped, save a profile field, add farmland, record a crop problem, add a note | **Read back + explicit yes.** "আপনি বললেন: 'সার দেওয়া শেষ'। আমি কি এই কাজটা শেষ হিসেবে রাখবো?" → spoken "হ্যাঁ" **or** tap ✓. Anything else = cancel. Shows a card with the exact values. |
| **T2 Irreversible / sensitive** | Delete farmland/data, close season, withdraw consent, delete recordings, share data | Read back + **tap ✓ required** (voice "হ্যাঁ" alone is not enough) + 5-second undo where possible. |

Mechanism: M5 persists its own chat/confirmation records but does not directly mutate another domain. Return a **ProposedAction** with exact farm/target/values; backend execution checks ownership, expiry, current state/season and replay protection before calling the owner. Expiry (proposed 10 minutes) is versioned/configured. **CCR-3.** Irreversible deletion cannot promise an undo after completion; any undo window must precede deletion or use a documented recoverable operation.

---

## 7. User Flows

Notation: 🗣 farmer speech, 🔊 app speech, 👆 tap alternative.

### F1 — First run, consent, voice lesson (P1)
1. App opens → 🔊 "আসসালামু আলাইকুম / নমস্কার। আমি ফিল্ডশিফট, আপনার খেতের সহকারী।" (greeting text decided with field team).
2. 🔊 Explain mic button with animation. 👆 "শুনুন" replays.
3. Consent C1, C2 (C3 optional) — §5.
4. OS mic permission.
5. Practice: 🔊 "বড় সবুজ বোতাম চাপুন, তারপর বলুন 'আজকের কাজ'।" Success → praise; failure → §4.6.
6. Offer widget setup (Android) with a helper (field agent / family).

### F2 — Navigate by voice (P1)
- 🗣 "আজকের কাজ" / "কাজ দেখাও" → Tasks (T0).
- 🗣 "সতর্কতা" / "আবহাওয়া" → Alerts; plays the top alert.
- 🗣 "ফসলের অবস্থা" → Crop health. 🗣 "পেছনে", "শুরুতে".
- 🗣 "উত্তরের জমি" → switch farmland (if ambiguous → tap choice).
- 👆 Same four big icons on Home; long-press speaks the name.

### F3 — Share farm details (M1 onboarding by voice) (P2)
1. M1 decides the next missing field (plan.md M1 "ask only for missing information").
2. 🔊 One question at a time: "আপনার জমি কতটুকু?"
3. 🗣 "দেড় বিঘা" → parser → 🔊 "দেড় বিঘা, ঠিক আছে?" + card [দেড় বিঘা] ✓ ✗ (T1).
4. Unit conversion question if needed (CCR-5).
5. 👆 Each question also has a picture-choice answer (e.g. soil type pictures, irrigation yes/no, water source icons) and a number pad with big digits.
6. 🗣 "ভুল হয়েছে, জমি দুই বিঘা" → correction proposal → T1 confirm.
7. 🗣 "পরে বলবো" → skip; M1 asks later.

### F4 — Ask a question (M5) (P2)
1. 🗣 "আলুর পাতা হলুদ হচ্ছে কেন?" → device STT (Tier 0; server STT at Tier 1) → transcript → M5 with farm context.
2. 🔊 Short grounded answer (≤ 2 sentences) + "আরও শুনতে চান?"
3. If M5 detects a disease-type question → offers F6: "একটা ছবি তুলবেন?" ✓ ✗.
4. If M5 detects an action ("সার দিয়েছি") → ProposedAction → T1 confirm.
5. Offline → queued; 🔊 "নেট এলে উত্তর দেবো।" Notification when answer arrives; tap → plays answer.

### F5 — Manage tasks (M3) (P2 read, P3 write)
1. 🗣 "আজকের কাজ কী?" → 🔊 "আজ ২টা কাজ। এক, সার দেওয়া। দুই, সেচ দেখা।"
2. 🗣 "প্রথমটা শেষ" / "সার দেওয়া হয়ে গেছে" → match task → 🔊 read back → T1 confirm → M3 updates status `completed`.
3. 🗣 "সেচ আজকে করবো না" → propose `skipped` (T1). 🗣 "কালকে মনে করিয়ে দিও" → propose reschedule if M3 supports farmer-sourced changes (task `source = 'farmer'` exists in the model).
4. 👆 Each task card: big ✓ "শেষ", ⏭ "বাদ", 🔊 "শুনুন". A tap on ✓ still shows the confirm card (T1) — prevents accidental taps.

### F6 — Scan or describe a crop problem (M6 → M3) (P3)
1. Entry: 🗣 "ফসলে সমস্যা" / 👆 camera icon / from F4.
2. 🔊 Photo coaching: "আক্রান্ত পাতা কাছে থেকে তুলুন। ছায়ায় না, আলোতে।" On-device blur/darkness check → 🔊 "ছবি ঝাপসা, আবার তুলুন।"
3. 🔊 "সমস্যাটা মুখে বলুন।" 🗣 "পাতায় বাদামি দাগ, দুই দিন ধরে" → transcript → M5 extracts `OptionalSymptoms` (existing M5→M6 contract).
4. Describe-only path stays in M5's grounded preliminary Q&A with uncertainty and a request for a photo/local help. Current M6 requires an image; do not invent an image diagnosis without an explicitly implemented, validated new contract.
5. M6 result → 🔊 plain-language confidence: High "সম্ভবত …", Moderate "হতে পারে …", Low "নিশ্চিত না। কৃষি অফিসারকে দেখান।" + 1–3 practical actions. Safety: no chemical dose by voice without the approved knowledge source; always suggest local extension officer for low confidence.
6. 🔊 "এই সমস্যাটা খাতায় তুলে রাখবো?" → T1 → M3 records Problem (status `open`). First implement CCR-11 so M6's current auto-write cannot precede confirmation; use an idempotent handoff and do not create the Problem twice.
7. Offline: eligible photo/transcript queued; audio only under §4.5's adapter/consent conditions. Later notifications require an implemented delivery path; a frontend-only queue cannot promise background delivery.

### F7 — Proactive alert listening (M4/M3) (P3)
1. Push notification (title in Bangla, short). Tap → app opens on the alert and plays it.
2. 🔊 "কাল ভারী বৃষ্টি হতে পারে। আজকের সেচ দরকার নেই।" → "সেচের কাজ বাদ দেবো?" → T1.
3. Notifications never auto-play audio while the app is closed (OS rules + privacy).

### F8 — Planting-window and rotation advice (M4 → M2 → M5/frontend)

1. Select farm/district and crop/season by tap or speech; clarify ambiguity and distinguish Aman advisory season from a duplicate Rice species.
2. Read the actual M2 `/advisory`/authenticated rotation result. Speak its short Bangla action/uncertainty first; show bilingual text, revised window and replay.
3. "কেন?" opens/speaks the two-period explanation, onset/GDD definitions and source limitations. Show distributions, GDD/sensitivity, sample counts, assumptions and dataset citations.
4. Compare current rotation plus two alternatives; changing water/soil/income priorities calls M2 and narrates its returned tradeoffs.
5. Copy/share the <160-character summary; confirm external composition/send and show Bangla SMS segment implications. No paid SMS gateway dependency.
6. Selecting/activating a scenario is a confirmed M2 action. M3 receives the agreed SeasonPlan/initial tasks; exploration does not mutate state. Missing evidence/no feasible window gives an explanation without an invented date.
7. Disconnected users see source-dated cached results or a clear absence; a queued request is not fresh satellite analysis.

### F9 — One useful question, robustness and confirmed Plan B (accepted follow-up)

1. After the required F8 flow works, render M2's A01 decision-driven question. Speak why this observable answer matters and offer the same typed choices by tap, including unknown/skip. Do not ask the farmer to guess lab-only values or repeat declined questions.
2. Read back the interpreted answer and farm name. An exploratory answer changes only a labeled scenario. Saving the answer is a distinct M1 ProposedAction; after confirmation, recompute from the saved authoritative snapshot. Confirming that answer cannot also select a crop or execute Plan B.
3. Read M2's A02 tested feasibility range with the binding crop/stage/constraint and uncertainty. Distinguish a bounded scenario result from a promise about crop survival, yield or tomorrow's weather. Allow text/list alternatives to the chart.
4. Show the selected plan's versioned contingency and source dates. When M2 reports a supported trigger, speak the reason, old/new dates and task diff from its A03 proposal. Missing/old/conflicting evidence gives a clear unavailable/review state, not an invented trigger.
5. Confirm or cancel using CCR-3; server verifies current owner/farm/season/plan/task revisions, freshness and expiry. Use transaction-aware M2/M3 operations and one execution receipt. Stale values require a new card/read-back; no automatic crop switch or completed-task rewrite. Preserve actual planting history.
6. An ambiguous “হ্যাঁ”, a farm switch, interrupted narration or an expired proposal cannot confirm a different/earlier action. Bind the response to the one visible current action. Replays of an already executed action return the saved outcome without duplicate changes.
7. Refresh the shared farm state after successful commit so tasks and farm-scoped chat agree. Offline shows the dated cached result; queued confirmation preserves its original payload/key/versions/expiry and revalidates on reconnect. An outdated action needs fresh review, never automatic reconfirmation.

The authoritative compute, policy, proposed persistence and execution specification is the [adaptive plan](2026-10-29-adaptive-decisions-and-confirmed-plan-b.md). Core F9 logic requires no paid AI/speech API.

---

## 8. Required Changes

### 8.1 Frontend (`frontend/`)

New, non-route code lives outside `src/app/` (AGENTS.md).

| Path (proposed) | Responsibility |
|---|---|
| `src/voice/VoiceProvider.tsx` | Voice session state machine: `idle → listening → processing → speaking → awaiting_confirmation`; one active session app-wide. |
| `src/voice/recorder.ts` | Audio capture (Opus), level meter, VAD end-point, max length. |
| `src/voice/recognizer.ts` | `SpeechRecognizer` interface; impls: `deviceRecognizer` (**Tier 0 default**, Android system engine, on-device or online), `serverRecognizer` (Tier 1/2, upload), `noopRecognizer` (tap mode). Capability check at startup selects the impl; config flag selects the tier. |
| `src/voice/commands.ts` + `src/voice/lexicon.bn.ts` | Command lexicon with dialect synonyms; normalizer; matcher returning top-N with scores. |
| `src/voice/parse.bn.ts` | Bangla numbers, fractions (দেড়/আড়াই/সোয়া/পৌনে), units, relative dates. Pure functions, unit-tested. |
| `src/voice/speaker.ts` | Plays bundled clips, device TTS (`expo-speech`), or server TTS audio; replay; rate setting. |
| `src/voice/prompts.ts` + `assets/audio/bn/*.opus` | Prompt IDs → bundled recordings + fallback text. |
| `src/components/MicButton.tsx` | Big fixed mic button with states, sound cues, accessibility label. |
| `src/components/ConfirmCard.tsx` | T1/T2 confirmation UI (values, ✓/✗, T2 requires tap, undo). |
| `src/components/ChoiceList.tsx` | Picture choices for unclear speech and tap mode. |
| `src/components/SpeakableButton.tsx` | Long-press → speak label; used to wrap `components/ui.tsx` buttons. |
| `src/i18n/` | Bangla-first strings (`expo-localization`), Bangla digits. Replace English strings in all screens. |
| Existing `src/services/api-client.ts` | Reuse typed requests, token provider and unauthorized handling; add bounded weak-network/offline behavior without a competing client. |
| `src/offline/queue.ts` | Persist eligible messages/photos/actions with tenant/farm/season scope, expiry, state version, idempotency and retry. Audio is conditional on §4.5. |
| `src/consent/` | Consent screens (spoken), state, withdraw. |
| `src/app/onboarding/*` | F1 first-run flow + voice lesson. |
| `src/app/listen.tsx` | Deep-link target `fieldshift://listen` → opens mic immediately. |
| `src/app/farmlands/[id]/crop-health.tsx` | Reuse current camera/upload/M6 result/history integration; add F6 coaching/description without duplicate scans/Problem writes. |
| `src/app/farmlands/[id]/tasks.tsx` | Reuse current API-backed tasks; add accessible controls/readback and confirmation before changes. |
| `src/components/FarmlandChat.tsx` | Add mic, play replies, show ProposedAction confirm cards, queued state. |
| `src/context/AppProvider.tsx` | Reuse existing API-backed auth/farm/chat state; add account-isolated persistent cache. |
| `app.json` | `name`/launcher label speakable Bangla; `scheme: "fieldshift"`; mic/camera permission strings in Bangla; config plugins for speech recognition, widget, shortcuts. |
| Widget / shortcuts | Android widget + app shortcuts via config plugin; iOS App Shortcuts / widget via config plugin or a small native target. Verify SDK 57-compatible libraries in Phase 0. |

Packages to evaluate (install with `npx expo install`, verify SDK 57; all free/open-source): `expo-speech-recognition` (MIT), `expo-audio`, `expo-speech`, `expo-camera` or `expo-image-picker`, `expo-localization`, `expo-notifications`, `expo-file-system`, `expo-network`, `expo-secure-store`, a persisted store (e.g. `expo-sqlite`), widget/shortcut libraries.

**Zero-cost build and distribution:** build the Android development/release APK locally (`npx expo run:android` / local Gradle release build) instead of paid cloud build minutes; install by direct APK. Play Store (one-time fee) and iOS distribution (paid Apple developer account) are deferred until funding (see §15).

Web build (`docker compose` Expo web) must keep working: voice degrades to tap-only or browser Web Speech where supported.

### 8.2 Backend (`backend/`)

| Path (proposed) | Owner | Responsibility |
|---|---|---|
| Existing `app/api/routes_m1_profile.py` + security/auth dependencies | M1 | Reuse password auth and owner-scoped profiles; no parallel auth store. |
| `app/api/routes_speech.py` | M5 | **Tier 1/2 only — not needed for zero-cost v1** (device does STT/TTS). `POST /v1/speech/transcribe` (multipart audio, `farmland_id`, `hint: command|free|description`) → `{transcript, alternatives[], confidence, duration_ms, provider}`. `POST /v1/speech/synthesize` `{text}` → audio (cached by hash). |
| `app/services/speech/` | M5 | Tier 1/2: `SttProvider` / `TtsProvider` interfaces; adapters for faster-whisper (`tugstugi` Whisper-medium), IndicConformer, `vits_rasa_13` / Indic Parler-TTS, optional cloud; Silero VAD + RNNoise; audio validation (type, size ≤ 2 MB, duration ≤ 60 s); delete audio after transcription unless consent C3. |
| Voice metadata on messages | M5 | Tier 0: the app sends the **transcript as text** plus `metadata.input_mode = "voice"`, `stt_engine = "android-system"`, `stt_confidence` (if the engine returns it). |
| Existing `app/api/routes_m5_chat.py`, `app/services/chat_engine.py`, `app/schemas/chat.py` | M5 | Extend existing routes additively with validated voice metadata, speech text, proposed actions and follow-up choices. Do not create duplicate `/v1` chat routes merely to follow obsolete example names. |
| Parent `/advisory` and authenticated M2 rotation result | M2 with M4 read-only input | Supply computed facts, bilingual sentence/SMS and assumptions/source IDs to F8; M5 renders rather than recalculates. |
| Adaptive result and policy reevaluation, same M2 rotation interface | M2 with M1/M4 read-only input; M3 operational execution | F9 question/robustness/contingency preview; reuse ProposedAction for exact confirmed diffs. Transaction-aware owner operations must replace naive chained committing calls before execution is enabled. |
| `app/api/routes_actions.py` + `app/services/actions/` | M5 (orchestration only) | `POST /v1/actions/{id}/confirm`, `/cancel`. On confirm, call the **owning module's** service (M1 profile update, M3 task status / problem create). Idempotency key required. |
| `app/api/routes_consent.py` | M1 | `GET/PUT /v1/farmers/me/consents`. |
| Object storage (dev: a self-hosted, free S3-compatible server in `docker-compose.yml`, or local disk volume for v1; check the server's license, e.g. AGPL terms) | Shared infra | Audio (only with C3) and crop photos (M6). |
| `app/services/nlu/` | M5 | Intent + slot extraction from Bangla transcripts; uses M2 crop catalogue (read-only) and M3 task list for matching. |
| `backend/tests/` | Each owner | Unit tests (parsers, confirmation state machine), contract tests (ChatResponse, ProposedAction), integration tests with Golden Farm. |
| `mock-data/farm-001/` | Shared | Add Bangla transcripts + expected intents/actions for voice tests. |
| Evaluation harness `backend/tools/stt_eval/` | M5 | Run candidates over the field dataset (Tier 0 Android engine transcripts collected on test phones + Tier 1 open models run on a laptop/free notebook); report WER/CER by region/noise. |

### 8.3 Data (see CCRs — none applied without team agreement)
- **Voice metadata without schema change (recommended first):** store voice messages as `message_type = 'text'` with the transcript in `message` and `metadata = {input_mode: "voice", stt_provider, stt_confidence, audio_retained: false}`. `attachment_key` set only when C3 = yes.
- `pending_actions` table (M5-owned): `id, conversation_id, farmer_id, farmland_id, action_type, target_module, payload jsonb, status (proposed|confirmed|cancelled|expired|executed|failed), confirm_method (voice|tap), idempotency_key unique, expires_at, created_at, executed_at`.
- `farmer_consents` (M1-owned): `id, farmer_id, consent_type, granted bool, text_version, method, granted_at, revoked_at`.
- Farmer preferences (M1): reuse existing `preferred_language`; add missing `voice_replies_enabled`/`speech_rate` only through documented contracts. Stored chat metadata does not imply `ChatMessageCreate` accepts arbitrary input: validate/allowlist voice fields explicitly.

---

## 9. Contract Change Requests (need team agreement — plan.md Rule C)

| ID | Change | Affects | Why |
|---|---|---|---|
| CCR-1 | Voice is an I/O channel inside M5 (speech endpoints owned by M5) | M5 scope | Avoid a 7th module; M5 already owns conversation input. |
| CCR-2 | Versioned consent persistence and missing preferences; reuse `preferred_language` | M1, shared contract | Specify additive storage/migration only where needed; no duplicate profile. |
| CCR-3 | `ProposedAction` contract + `pending_actions`; M5 may *propose*, owning module *executes* | M1, M3, M5, M6 | Mandatory confirmation without M5 owning data. |
| CCR-4 | `ChatResponse` adds `speech_text`, `proposed_actions`, `follow_up_choices` | M5 contract | Spoken replies and tap alternatives. |
| CCR-5 | Accept বিঘা/কাঠা/শতাংশ input with farmer-confirmed local conversion | M1, DB_SCHEMA `land_area_display_unit` | Farmers speak local units. |
| CCR-6 | Optional later: `chat_messages.message_type` adds `audio` | Shared schema | Only if audio messages must be first-class; metadata approach avoids it. |
| CCR-7 | Object storage service in dev/prod stack | Infra | Photos (M6) and opt-in audio. |
| CCR-8 | Bangla crop/variety synonyms in M2 catalogue | M2 | Speech matching for crop names. |
| CCR-9 | Android-first without purchased speech API, capability fallback and measured release costs | All modules | No universal offline-Bangla/iOS-STT or indefinitely free production promise. |
| CCR-10 | Typed M2 advisory/rotation and M4 district climate input; confirmed M2 selection | M1/M2/M3/M4/M5 | Parent §§4/8; retain routes/ownership, no operational writes from district queries. |
| CCR-11 | Reconcile M6 scan auto-problem behavior with F6 confirmation | M3/M5/M6 | Prevent pre-confirmation and duplicate writes; a later UI card cannot fix today's scan side effect. |
| CCR-12 | A01 question/A02 envelope/A03 contingency result, versioned policy/proposal, M1 answer provenance and atomic M2/M3 apply through CCR-3 | M1/M2/M3/M4/M5, shared DB/infra | Owner accepted product scope; [adaptive specification](2026-10-29-adaptive-decisions-and-confirmed-plan-b.md) §§3-9 define contract/migration review, one-time execution, stale-state handling and A01-A08 gates. No second confirmation store or automatic crop change. |

---

## 10. Module Dependencies

```text
Existing foundation: Auth + API client ── source/contract fixtures ── Bangla i18n
                                   │
            ┌──────────────────────┼─────────────────────────────┐
            ▼                      ▼                             ▼
   Voice shell (frontend,   M5 Speech API (STT/TTS)      Consent (M1, CCR-2)
   Tier 0 device STT/TTS)   [Tier 1 only, Phase 6]
            │                      │                             │
            └──────────┬───────────┘                             │
                       ▼                                         │
          M5 Chat + NLU + ProposedAction (CCR-3/4) ◄─────────────┘
              │          │            │             │
     reads M1 profile  reads M3    reads M2      routes to M6
     writes via M1     writes via  crop names    (image + OptionalSymptoms)
     (F3)              M3 (F5,F6)  (CCR-8)              │
                                                        ▼
                                              M6 result → M3 Problem (T1)
            Voice launch (widget/shortcuts/deep links) depends only on the voice shell.
            Offline queue depends on API client + idempotent actions.
            M4 district caches → M2 window/rotation → M5 explanation (F8).
            Confirmed choice → M2 SeasonPlan → M3 operational tasks/state.
            After core delivery: M2 field question → confirmed M1 fact → revised M2 envelope.
            Dated M4 evidence → M2 policy/diff → M5 confirmation → atomic M2/M3 apply (F9).
```

Each module keeps working against mocks (plan.md §6); voice tests use `mock-data/` transcripts.

---

## 11. Implementation Phases (prioritized)

### Phase 0 — Spikes, prerequisites, agreements (P0, blocks everything)
- [ ] Verify the parent plan's data/compute/result prerequisites for F8 and create consented Bangla command/advisory examples with known failure cases.
- [ ] **Tier 0 go/no-go spike:** use borrowed low-end Android phones including Android 10–12 and 13+, 2–4 GB RAM; apply version-appropriate capability checks (§4.1), online/on-device/model-download tests, installed Bengali TTS and mic interruption/background checks. Record actual devices/results. Wider 6–8-phone/iOS coverage is a broader-rollout gate, not fabricated demo evidence.
- [ ] Collect an initial consented speech/usability sample and report actual people/devices/noise. The ≥8-region/≥20-speaker-per-region study is a separate Phase 5/§12 gate, not a prerequisite for the initial 48-hour advisory slice.
- [ ] STT evaluation on that dataset: **Tier 0** Android engine (transcripts collected on the test phones) vs **Tier 1** open models (`tugstugi` Whisper-medium, IndicConformer) run on a laptop or free notebook tier. Report WER/CER per region & noise. Decision: is Tier 0 good enough for v1 commands and short answers?
- [ ] TTS listening test with 15+ farmers: team-recorded prompts vs Android system TTS (vs Tier 1 open TTS sample) — comprehension + preference.
- [ ] Record the bundled prompt set (team/volunteer voice, signed voice release).
- [ ] Record affected-owner implementation decisions for CCR-1…CCR-12; this planning update is not evidence that the team has already signed off.
- [ ] Verify existing auth/API integration, reuse source/contract fixtures, produce a local native Android build and agree the actual app name/scheme.
- [ ] Privacy review of consent text (Tier 0 disclosure of the phone's speech service).

**Acceptance:** measured capability report; tap fallback/provisioned alternative when speech fails; contract decisions recorded; native build runs on a phone; available confidence signals calibrated or explicitly absent; core recordings and typed advisory narration verified. Record actual resources/spend rather than declaring zero total production cost.

### Phase 1 — Accessible voice shell + navigation (P1)
- [ ] Bangla-first UI (i18n), large targets (≥ 56 dp), icons + SpeakableButton, Home "আজকে কী করবো".
- [ ] Consent flow F1 and voice lesson.
- [ ] MicButton, `deviceRecognizer` (Tier 0) + `noopRecognizer`, `SpeechRecognizer` interface ready for `serverRecognizer`, speaker with bundled prompts + system TTS, VoiceProvider state machine.
- [ ] Command lexicon + matcher; navigation F2; unclear-speech rules §4.6.
- [ ] iOS and phones without Bangla STT: tap-first UI with spoken prompts (no mic button shown, or mic shows "এই ফোনে কথা বোঝা যায় না" once).
- [ ] Offline indicator; cached Home summary.

**Acceptance:**
- All navigation commands (≥ 15) recognized top-1 ≥ 90% in quiet and ≥ 80% in field noise on the Phase 0 test set (targets — adjust after Phase 0).
- Every screen usable with mic permission denied (tap-only), verified by test script.
- Mic never active without visible "শুনছি" state; no mic use when app is backgrounded (automated + manual check on Android 14+).
- Usability: ≥ 8 of 10 low-literacy test farmers reach Tasks and Alerts by voice and by tap without help.

### Phase 2 — Read flows + Q&A + voice onboarding (P1)
- [ ] F8: speak/replay the actual planting-window and rotation result with source facts, uncertainty, chart/evidence links and bilingual/SMS consistency; meet parent V06/V10/V11 gates.
- [ ] After the required core flow, F9 reads M2's question and tested envelope, distinguishes hypothetical from saved answers, and supports unknown/skip/read-back without paid reasoning APIs. Record adaptive A01/A02/A07 evidence.
- [ ] F4 ask a question via M5 (mock M1/M2/M3 context) with spoken short answer, "আরও", replay.
- [ ] F5 read tasks; F7 read alerts.
- [ ] F3 farm details by voice with Bangla number/unit/date parser and picture-choice alternatives.
- [ ] ConfirmCard + ProposedAction (CCR-3/4) for F3 saves.

**Acceptance:**
- Parser unit tests: ≥ 200 Bangla number/unit/date cases pass (দেড়, আড়াই, সোয়া, পৌনে, বিঘা, শতাংশ, পরশু …).
- Zero profile writes without a confirmed ProposedAction (contract test + DB assertion).
- Median voice round trip (5-s question → first audio of answer) ≤ 6 s on simulated 3G; ≤ 3 s for cached/bundled prompts.
- Tier 0 check: no paid API call anywhere in the flow (network log review).

### Phase 3 — Write flows + crop problems (P1)
- [ ] F5 mark done/skip/reschedule with T1 confirmation; idempotent execution in M3.
- [ ] F6 photo coaching, blur check, spoken description → M6 `OptionalSymptoms` → spoken result → T1 → M3 Problem.
- [ ] T2 actions (delete, withdraw consent, delete recordings) require tap.
- [ ] Offline queue for messages, photos, confirmed actions.
- [ ] After core delivery and adaptive D1-D3, complete F9's Plan B diff/confirmation, atomic owner execution, saved receipt/retry and scoped state refresh. Enable execution only after adaptive A03-A06 concurrency/rollback checks; validate A07-A08 with browser and actual Android use.

**Acceptance:**
- Automated tests: for every write intent, no state change before confirm; cancel/timeout leaves state unchanged; retry with same idempotency key applies once.
- T2 cannot complete by voice alone (test).
- Golden-flow (plan.md §7) runs on mocks and real integration: advisory/rotation → confirmed selection → season plan → M3 tasks → question/photo → disease result → problem visible in next answer. Clean-user activation uses actual approved stage/task data; synthetic fixtures remain test-only.
- Queued items survive app restart and sync once on reconnect.

### Phase 4 — Voice launch entry points (P2)
- [ ] Deep links: `fieldshift://listen`, `fieldshift://farm/{id}/tasks`, `/alerts`, `/camera`.
- [ ] Android widget (big mic) + app shortcuts; notification tap → open + play.
- [ ] Spoken "how to open me" lesson; setup guide for field agents.
- [ ] *(Deferred to funded stage)* iOS App Shortcuts (App Intents) + widget; Siri phrase in English documented. Needs a paid Apple developer account for distribution.

**Acceptance:** widget tap → listening within 2 s on a low-end test phone (cold start ≤ 4 s); no mic start without the user action; shortcuts work on Android 10–15 test devices.

### Phase 5 — Field pilot and tuning (P2)
- [ ] Complete the consented ≥8-region/≥20-speaker-per-region study with mixed age/gender, quiet/field noise and actual WER/CER/task results. Do not imply completion in the initial 48-hour milestone.
- [ ] Pilot with 40–60 farmers across regions for 3–4 weeks (§12).
- [ ] Expand dialect lexicon; tune thresholds, speech rate, reply length.
- [ ] Measure and fix top failure intents.

**Acceptance:** task success ≥ 85% for F2/F4/F5 by voice-or-tap; ≤ 1 wrong saved action per 200 confirmed actions (target) and zero unconfirmed writes; farmer-reported understanding of spoken replies ≥ 80%.

### Phase 6 — Tier 1 upgrade and optional improvements (P3, needs hosting budget)
- [ ] Self-host Tier 1 STT/TTS (`routes_speech.py`, `app/services/speech/`) with open-source models; fine-tune on consented field data (C3) if Tier 0 accuracy is weak for some regions.
- [ ] Switch recognizer by config flag; A/B compare Tier 0 vs Tier 1 on the pilot dataset.
- [ ] iOS voice (server STT) + iOS distribution; Play Store listing.
- [ ] Quick Settings tile / Control Center; audio messages as first-class (CCR-6).

**Acceptance:** Tier 1 beats Tier 0 WER/CER on the field dataset before switching; switching needs no app-flow change (same interface).

---

## 12. Field-Testing Needs

- **Regions/dialects (minimum):** Chattogram (Chatgaiya), Sylhet (Sylheti), Noakhali, Barishal, Rangpur, Rajshahi/Varendra, Mymensingh, Khulna/Jashore; plus a central/standard-Bangla control group. Indigenous languages (e.g. Chakma, Santali, Garo) are **out of scope** for v1 (assumption A3) — record the gap.
- **People:** women and men; ages 18–70+; low/no literacy; first-time smartphone users; farmers using a family member's phone.
- **Devices:** low-end Android (2–3 GB RAM, Android Go where possible), older Android 10–12, mid-range Android 14–15, 1–2 iPhones.
- **Conditions:** open field with wind, near running irrigation pump, rain on tin roof, home with TV, market. Headset vs no headset.
- **Network:** no signal, 2G/EDGE, unstable 3G/4G, data-saver on, low balance.
- **Method:** task-based sessions with a facilitator speaking local dialect; think-aloud is hard for this group → observe + short follow-up questions; log anonymized interaction events (with consent).
- **Ethics:** verbal + recorded informed consent in Bangla; separate consent for audio dataset; compensation for time; data stored securely, deletable on request; partner with local agriculture extension staff and community organizations (assumption A6).
- **Metrics:** WER/CER by region & noise, command top-1 accuracy, task success, time on task, clarification count per task, confirmation error rate, abandoned sessions, comprehension of spoken replies (teach-back).

---

## 13. Assumptions (verify)

| ID | Assumption |
|---|---|
| A1 | Most target farmers use Android; iOS is secondary. Verify with pilot recruitment data. |
| A2 | Target users speak a Bangla dialect and understand standard Bangla when spoken slowly. |
| A3 | Indigenous languages are out of scope for v1. |
| A4 | Many phones are shared within a family. |
| A5 | Farmers have intermittent mobile data, often 2G/3G, sometimes none for hours. |
| A6 | Field agents / extension staff / family can help with install, consent, and widget setup. |
| A7 | The Android system engine (Tier 0) reaches acceptable Bangla accuracy for commands and short answers; if not, a Tier 1 open model does. Phase 0 decides. |
| A8 | Provider confidence scores are usable for thresholds after calibration. |
| A9 | Tap is required for legal consent; voice "হ্যাঁ" is supporting evidence only (legal review). |
| A10 | Bangladesh personal-data rules apply to voice and farm data; current law to be checked before launch. |
| A11 | Gemini/Assistant "open app" in Bengali may or may not work; not a dependency. |
| A12 | Existing auth/M1-M6 APIs are reused. Clean-user season knowledge, NASA advisory/rotation and additive voice/action interfaces still need implementation/verification. |
| A13 | No purchased speech API is the pilot target. Hosting, durable data, distribution and operating capacity are measured; free tiers/donated machines do not establish indefinite free production. |
| A14 | Most pilot phones have Google's speech services and a Bengali TTS voice installed (Phase 0 verifies). |
| A15 | Free tools stay free and their terms allow this use (device speech services, open model licenses). Re-check before launch. |

## 14. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Poor Bangla STT for regional dialects | Core experience fails | Phase 0 evaluation on field data; command lexicon with synonyms; tap fallback after 2 failures; never guess on writes; Tier 1 fine-tuned open model as upgrade path. |
| Tier 0 engine cannot be tuned or controlled | Accuracy plateau; vendor may change behavior | Keep `SpeechRecognizer` interface; Tier 1 ready as fallback; monitor clarification rate. |
| Tier 0 sends audio to the phone's speech vendor | Privacy concern | Clear C2 disclosure; prefer on-device recognition when available; Tier 1 keeps audio on our server. |
| Actual device has no usable Bangla recognition/voice | Missing or wrong-language output | Capability-based tap-first UI, verified voices/prompts and optional provisioned server adapter; never silently change language. |
| Android `bn-BD` support varies by phone/OEM | Some phones get no voice | Runtime capability check; tap mode; offline queue. |
| Zero budget for hosting during pilot | Backend downtime | Run on team machine for small pilot; keep app useful offline with cached data. |
| Using a non-commercial model by mistake | Legal risk | License rule in Global Constraints; license check in code review. |
| Wrong action saved from misheard speech | Wrong farm records, bad advice | T1/T2 confirmation, read-back of numbers, idempotency, undo, audit trail. |
| Weak network → slow replies | Users give up | Bundled prompts, cached Home, queue + notification, compact audio, short timeouts with spoken status. |
| Privacy fear of "listening phone" | Low adoption | No wake word, visible/audible mic state, no audio retention by default, easy withdraw. |
| Cost when users grow beyond pilot | Capacity/availability shortfall | Device speech avoids purchased calls; measure backend/storage/inference/data costs, cache appropriately and provision before scaling. |
| Unsafe agronomic advice read aloud (pesticide doses) | Harm | Answers only from approved knowledge (plan.md M5, DB_SCHEMA provenance); low-confidence → extension officer. |
| Cross-module contract changes not agreed | Blocks phases 2–3 | Raise CCRs in Phase 0; build against mocks meanwhile. |
| Expo SDK 57 library compatibility (speech, widgets) | Rework | Verify in Phase 0 dev build; config plugins only. |
| Low-end phones: memory/battery | Crashes, slow | No always-on listening, no large on-device models in v1, test on 2 GB devices. |

## 15. Open Decisions for the Team
1. Record CCR-1…CCR-12 implementation decisions with affected owners, including M4/M2 analytical input, M6 confirmation reconciliation and the accepted adaptive policy/atomic execution contracts. Product direction is owner-authorized; do not claim migration/teammate signoff without a record.
2. Verify existing auth and season-data prerequisites; document additive schema/interfaces rather than redesigning auth.
3. App display name and deep-link scheme (must be easy to say in Bangla).
4. Tier 0 go/no-go after Phase 0; when to move to Tier 1 (hosting source and budget).
5. Voice talent for recorded prompts and greeting wording (volunteer, signed release).
6. Pilot regions and partner organizations.
7. When to pay for Play Store / Apple developer accounts (deferred; not needed for APK pilot).

## Sources and verification status

The original 2026-10-06 links below are background references, not proof of current capability. The [feasibility review](../research/2026-10-28-free-mobile-voice-feasibility.md) records native speech/build/cost checks; the [2026-10-29 parent plan](2026-10-29-nasa-planting-window-and-rotation.md) records organizer/science requirements. Recheck matching Expo SDK 57 docs and actual devices before native implementation. Model ports/anecdotes below are candidates to verify, not established license/benchmark evidence.
- Android foreground service types / while-in-use microphone: https://developer.android.com/develop/background-work/services/fgs/service-types , https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start
- Android 17 background audio hardening: https://developer.android.com/about/versions/17/changes/bg-audio
- Android hotword detection is a system API: https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/java/android/service/voice/HotwordDetectionService.java
- Siri Indian multilingual mode (Bangla mixed with English only): https://support.apple.com/en-us/105012
- iOS 27 feature availability (Bangla keyboards, Bengali VoiceOver/Live Speech): https://www.apple.com/ios/feature-availability/
- expo-speech-recognition (wraps SFSpeechRecognizer / Android SpeechRecognizer): https://github.com/jamsch/expo-speech-recognition
- Bengali voice dialer experience (small Whisper → Devanagari): https://dev.to/devksarkar/i-tried-to-build-a-bengali-voice-dialer-for-android-here-is-what-actually-happened-and-how-i-40ak
- Gemini mobile app languages/countries: https://support.google.com/gemini/answer/14579026?hl=en&co=GENIE.Platform%3DAndroid
- Gemini Live API languages (bn-BD): https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/configure-language-voice
- AI4Bharat IndicConformer (MIT): https://github.com/AI4Bharat/IndicConformerASR , https://huggingface.co/ai4bharat/indic-conformer-600m-multilingual
- BengaliAI `tugstugi` Whisper-medium (Apache-2.0, derived ports): https://huggingface.co/winshades/bengaliai-whisper-medium-ggml , https://huggingface.co/psdn-ai/bangla-asr
- Bangla long-form ASR comparison (tugstugi lowest WER): https://arxiv.org/html/2603.03158
- Indic Parler-TTS (Apache-2.0): https://huggingface.co/ai4bharat/indic-parler-tts
- Meta MMS-TTS Bengali (CC-BY-NC 4.0 — do not use): https://huggingface.co/facebook/mms-tts-ben
