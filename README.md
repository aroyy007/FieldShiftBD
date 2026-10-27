<p align="center">
  <img src="frontend/assets/images/icon.png" alt="FieldShift BD" width="100" />
</p>

<h1 align="center">🌾 FieldShift BD</h1>

<p align="center">
  <strong>AI-Powered Farm Management Assistant for Bangladesh</strong>
</p>

<p align="center">
  An intelligent, conversational farm assistant that guides Bangladeshi farmers through the entire crop season — from onboarding and crop selection to daily task management, weather-aware alerts, crop disease detection, and harvest planning.
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-modules">Modules</a> •
  <a href="#-api-reference">API Reference</a> •
  <a href="#-setup--installation">Setup</a> •
  <a href="#-environment-variables">Environment</a> •
  <a href="#-testing">Testing</a>
</p>

---

## 📖 Overview

FieldShift BD is **not simply "ChatGPT for farmers."** It is an **AI farm manager with a conversational interface**, designed specifically for Bangladeshi agriculture.

The system understands a farmer's complete context:

```
Who is the farmer? → Where is the farm? → What resources are available?
→ What crop is being grown? → What growth stage is the crop in?
→ What tasks are due? → What problems are open? → What is the weather doing?
→ What does the farmer need to know or do next?
```

### Key Features

| Feature | Description |
|---|---|
| **Progressive Onboarding** | Conversational profile building — asks only what's missing, allows corrections |
| **Crop Advisory** | Explainable crop recommendations based on soil, climate, irrigation, budget, and BARC-sourced agricultural knowledge |
| **Rotation Comparison** | Comparison of BRRI-published crop sequences against saved farm context and farmer priorities, without an unsupported soil-health score |
| **Season Planning** | Growth-stage definitions, task scheduling, and harvest guidance |
| **Farm Brain** | Central state engine tracking tasks, problems, check-ins, and growth stages |
| **Weather Intelligence** | Real-time weather alerts from Open-Meteo & NASA POWER, with smart suppression — alerts only when weather changes what the farmer should do |
| **Disease Detection** | Photo-based crop disease screening using a ResNet-50 CNN (94 classes) with optional Gemini AI verification |
| **AI Chat** | Context-grounded conversational assistant powered by Gemini, aware of farm profile, crop state, tasks, and problems |
| **Bilingual UI** | English and বাংলা (Bangla) language support |

---

## 🚀 Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v4.0+)
- Git

### 1. Clone & Configure

```bash
git clone <REPOSITORY_URL>
cd FieldShiftBD-main
```

Copy the environment template and generate a JWT secret:

```bash
# Linux / macOS
cp .env.example .env
cp backend/.env.example backend/.env

# Generate a SECRET_KEY and add it to backend/.env
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> backend/.env
```

```powershell
# Windows PowerShell
Copy-Item .env.example .env
Copy-Item backend\.env.example backend\.env

python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> backend\.env
```

> [!IMPORTANT]
> The `SECRET_KEY` in `backend/.env` **must** be set to a non-empty random value. The backend will refuse to start without it.

### 2. Build & Run

```bash
docker compose up --build
```

### 3. Access the Application

| Service | URL |
|---|---|
| 🌐 Frontend (Expo Web) | http://localhost:8082 |
| 🔌 Backend API | http://localhost:8000 |
| 📚 API Documentation (Swagger) | http://localhost:8000/docs |
| 💚 Health Check | http://localhost:8000/health |

After the first build, start the stack with `docker compose up`. Stop with `Ctrl+C` or `docker compose down`.

> [!CAUTION]
> PostgreSQL data is stored in a named Docker volume. Do **not** run `docker compose down -v` unless you intend to delete all database data.

---

## 🏗 Architecture

### Six-Module Architecture

The system is built as six independent modules connected through shared database contracts and a central farm state hub:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          SHARED CONTRACTS (DB)                          │
├────────────┬────────────┬────────────┬────────────┬──────────┬──────────┤
│  Module 1  │  Module 2  │  Module 3  │  Module 4  │ Module 5 │ Module 6 │
│   Farm     │   Crop     │   Farm     │  Weather   │   Chat   │ Disease  │
│  Profile   │  Advisor   │   Brain    │   Intel    │  Layer   │ Detect   │
│            │            │  (Hub)     │            │          │          │
└────────────┴────────────┴────────────┴────────────┴──────────┴──────────┘
```

#### Data Flow

```
Farm Onboarding (M1) → Crop Recommendation (M2) → Crop Selected (M2)
    → Season Plan (M2) → Tasks Created (M3) → Weather Affects Task (M4)
    → Weather Alert (M4) → Farmer Asks Question (M5) → Contextual Answer (M5)
    → Farmer Uploads Photo (M6) → Disease Detected (M6)
    → Problem Written to Farm Brain (M3) → Visible in Chat & Check-ins
```

### Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic |
| **Frontend** | React Native (Expo SDK 57), TypeScript, Expo Router |
| **Database** | PostgreSQL 16 |
| **ML Model** | PyTorch (ResNet-50), 94-class crop disease classifier |
| **AI** | Google Gemini API (chat + disease verification) |
| **Weather** | Open-Meteo API + NASA POWER API |
| **Auth** | JWT (HS256) + Argon2id password hashing |
| **Deployment** | Docker Compose (3 services) |

---

## 📦 Modules

### Module 1 — Farm Profile & Onboarding

**Owner:** Farmer/farm data, progressive onboarding conversation.

The onboarding engine tracks which profile fields are filled and determines the next question to ask. The chat (Module 5) drives this question-by-question. Location names are canonicalized against the BARC crop-zoning location list with BBS geocodes.

**Key capabilities:**
- Farmer registration and JWT authentication (phone + password)
- Multi-farmland management (one farmer, many fields)
- Stateful onboarding with percent-complete tracking
- Division/district/upazila resolution with spelling alias normalization
- Soil texture and land type validation against reference vocabulary

### Module 2 — Crop Advisor & Season Lifecycle

**Owner:** Crop suitability reasoning, season plans, growth stages, harvest guidance.

Recommendations are **explainable** — every crop suggestion includes structured reasoning (soil match, timing, irrigation, climate, budget) sourced from approved BARC agricultural knowledge. Raw scores are supplementary, not primary.

**Key capabilities:**
- Crop recommendation engine with multi-factor suitability scoring
- Read-only comparison of source-backed crop sequences using saved farm context and explicit farmer priorities
- Displays sequence, crop/fallow slots, applicability notes, and source links; it does not estimate soil-health outcomes or create seasons/tasks
- Support for BARC-sourced knowledge with provenance tracking
- Season creation with crop selection and variety support
- Growth stage definitions and season plan generation
- Harvest guidance per crop and season
- Season outcome recording and history

### Module 3 — Farm Brain (Task & Monitoring Engine)

**Owner:** Central operational state of the farm.

This is a **state engine + scheduler**, not a content-generation feature. All other modules read from and/or write to Module 3's state. `FarmState` is an API view assembled from normalized records — there is no separate persisted state blob.

**Key capabilities:**
- Task CRUD with lifecycle tracking (pending → completed / skipped / cancelled)
- Derived schedule states: due, overdue, upcoming (computed at query time)
- Bulk task import from season plans with idempotent `source_reference` keys
- Problem tracking with severity and status management
- Farmer check-in recording with observations
- Growth stage progression updates
- Composite farm state endpoint aggregating all operational data

### Module 4 — Weather Intelligence & Alerts

**Owner:** Weather data processing and actionable, context-aware alerts.

The system does **not** simply notify "rain tomorrow." It determines whether the rain changes what the farmer should do. A suppression engine filters out irrelevant weather events.

**Key capabilities:**
- Dual weather providers: Open-Meteo (7-day forecast) + NASA POWER (30-day observed data)
- Rotation comparisons also fetch a separate 25-complete-year NASA POWER daily history (T2M and PRECTOTCORR); it is descriptive context, not a sequence score
- Parallel upstream fetching with fault tolerance
- Crop-aware, growth-stage-aware alert generation
- Smart alert suppression (e.g., rain alert suppressed if no irrigation task is due)
- Real farmland coordinates via M1 profile (lat/lon from GPS or manual entry)
- Demo endpoint for deterministic testing without network calls

### Module 5 — Conversational Layer

**Owner:** Main chat interface and message routing.

Every response is grounded in the farmer's full context — farm profile, current crop, growth stage, tasks, problems, and agricultural knowledge. The chatbot is an intelligent router, not a generic LLM.

**Key capabilities:**
- Intent detection and routing (onboarding, task queries, farm state, weather, disease)
- Full farm context aggregation for grounded responses
- Gemini-powered AI responses with agricultural knowledge injection
- Conversation thread management per farmland
- Quick chat endpoint (auto-creates/reuses conversations)
- Onboarding-driven conversation flow
- Message deduplication via `client_request_id`

### Module 6 — Disease Detection

**Owner:** Image-based crop disease analysis.

Uses a custom-trained ResNet-50 model (`Saon110/bd-crop-vegetable-plant-disease-model`) with 94 classes covering crops common in Bangladesh. Optional Gemini verification provides a second opinion.

**Key capabilities:**
- Image upload with validation (JPEG/PNG/WebP, 10 MB limit, minimum 128px)
- ResNet-50 inference with softmax probabilities
- Crop mismatch detection (predicted crop vs. active season crop)
- Confidence thresholding with configurable threshold (default: 0.70)
- Optional Gemini AI verification (dual-model consensus)
- Automatic problem creation in Module 3 farm state
- Retry mechanism for failed Module 3 problem syncs
- Structured response with disclaimer and recommended actions

---

## 📡 API Reference

### System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Welcome message |
| `GET` | `/health` | Health check (includes database connectivity) |

### Auth (Module 1)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new farmer (name + phone + password) → returns JWT |
| `POST` | `/auth/login` | Login with phone + password → returns JWT |

### Profile & Farmlands (Module 1)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/profile` | Full profile (farmer + all farmlands) | ✅ |
| `PATCH` | `/profile/farmer-profile` | Update experience, equipment, livestock | ✅ |
| `GET` | `/farmlands` | List all farmer's farmlands | ✅ |
| `POST` | `/farmlands` | Create a new farmland | ✅ |
| `GET` | `/farmlands/{id}` | Get a farmland's full profile | ✅ |
| `PATCH` | `/farmlands/{id}` | Update farmland fields | ✅ |
| `GET` | `/farmlands/{id}/onboarding-status` | Onboarding completion status & next question | ✅ |

### Crop Catalog & Reference (Module 1)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/crops` | Full crop catalog with varieties | — |
| `GET` | `/crops/{id}` | Single crop with varieties | — |
| `GET` | `/reference/locations` | Bangladesh divisions/districts/upazilas | — |
| `GET` | `/reference/profile-vocabulary` | Soil textures, land types, area units | — |

### Crop Advisor (Module 2)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/advisor/recommendations` | Generate crop recommendations | ✅ |
| `POST` | `/advisor/farmlands/{id}/recommendations` | Recommend crops for a farmland | ✅ |
| `GET` | `/advisor/farmlands/{id}/recommendations` | List recommendations | ✅ |
| `POST` | `/advisor/farmlands/{id}/rotation-comparisons` | Compare source-backed crop sequences and include historical NASA POWER climate context (read-only) | ✅ |
| `POST` | `/advisor/recommendations/{id}/dismiss` | Dismiss a recommendation | ✅ |
| `POST` | `/advisor/seasons` | Select crop and create season | ✅ |
| `GET` | `/advisor/farmlands/{id}/seasons` | Season history | ✅ |
| `POST` | `/advisor/seasons/{id}/activate` | Activate a season | ✅ |
| `POST` | `/advisor/seasons/{id}/plan` | Generate season plan | ✅ |
| `GET` | `/advisor/seasons/{id}/plan` | Get season plan | ✅ |
| `GET` | `/advisor/seasons/{id}/harvest-guidance` | Harvest guidance | ✅ |
| `POST` | `/advisor/seasons/{id}/close` | Close season with outcome | ✅ |

### Farm State (Module 3)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/farmlands/{id}/state` | Full farm state (season, tasks, problems, check-ins) | ✅ |
| `GET` | `/farmlands/{id}/tasks` | List tasks (filterable by status, schedule state) | ✅ |
| `POST` | `/farmlands/{id}/tasks` | Create a task | ✅ |
| `GET` | `/farmlands/{id}/tasks/{taskId}` | Get a single task | ✅ |
| `PATCH` | `/farmlands/{id}/tasks/{taskId}` | Update task status | ✅ |
| `POST` | `/farmlands/{id}/seasons/{seasonId}/tasks/from-plan` | Bulk import tasks from season plan | ✅ |
| `GET` | `/farmlands/{id}/problems` | List problems (filterable by status) | ✅ |
| `POST` | `/farmlands/{id}/problems` | Create a problem | ✅ |
| `GET` | `/farmlands/{id}/problems/{problemId}` | Get a single problem | ✅ |
| `PATCH` | `/farmlands/{id}/problems/{problemId}` | Update problem status | ✅ |
| `GET` | `/farmlands/{id}/check-ins` | List check-ins | ✅ |
| `POST` | `/farmlands/{id}/check-ins` | Record a check-in | ✅ |
| `PATCH` | `/farmlands/{id}/state/growth-stage` | Update current growth stage | ✅ |

### Weather (Module 4)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/weather/assessment/{id}` | Weather assessment with actionable alerts | ✅ |
| `GET` | `/weather/assessment/{id}/demo` | Offline demo (mock weather, no network) | — |
| `GET` | `/weather/raw/{id}` | Raw provider data (debug only) | ✅ |

### Chat (Module 5)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/farmlands/{id}/conversations` | Create a conversation thread | ✅ |
| `GET` | `/farmlands/{id}/conversations` | List conversations | ✅ |
| `GET` | `/farmlands/{id}/conversations/{convId}` | Get conversation with messages | ✅ |
| `POST` | `/farmlands/{id}/conversations/{convId}/messages` | Send message & get AI response | ✅ |
| `POST` | `/farmlands/{id}/chat` | Quick chat (auto-manages conversation) | ✅ |

### Disease Detection (Module 6)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/farmlands/{id}/disease-results` | Upload image → analyze disease | ✅ |
| `POST` | `/farmlands/{id}/disease-results/{resultId}/sync-problem` | Retry Module 3 problem sync | ✅ |
| `GET` | `/farmlands/{id}/disease-results` | List disease analysis history | ✅ |

> [!TIP]
> All authenticated endpoints require the header: `Authorization: Bearer <JWT_TOKEN>`. Tokens are valid for 90 days.

---

## 🛠 Setup & Installation

### Option A: Docker Compose (Recommended)

This is the simplest way to run the full stack. See [Quick Start](#-quick-start) above.

**Services started:**

| Service | Container | Port |
|---|---|---|
| PostgreSQL 16 | `fieldshift-db-1` | `5433` (host) → `5432` (container) |
| FastAPI Backend | `fieldshift-backend-1` | `8000` |
| Expo Frontend | `fieldshift-frontend-1` | `8082` |

On first boot, the backend container automatically runs `alembic upgrade head` to apply all database migrations.
The Compose backend mounts the named `fieldshift_nasa_power_cache` volume at `/data/nasa-power`. For deployments outside Compose, mount persistent storage and set `NASA_POWER_CACHE_DIR`; otherwise the default temporary directory will not survive container replacement.
For an offline demo, run one rotation comparison while connected so the daily history is cached; subsequent requests use the mounted disk cache. `NASA_POWER_REFRESH_CACHE=1` refreshes the current history and should be turned off again after refreshing.

Historical rotation context uses the [NASA POWER Daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) for daily mean 2 m temperature (`T2M`) and corrected precipitation (`PRECTOTCORR`). NASA documents daily UTC/LST data from 1981 to near real time; FieldShift requests the latest 25 complete calendar years and splits them into earlier/later comparison periods. A year or year-month contributes to averages only at 90% or higher daily coverage; all observed coverage remains visible. The response reports its requested and observed years, data coverage, retrieval timestamp, and whether values came from a live fetch, live-but-uncached request, disk cache, stale cache, or were unavailable. POWER meteorological data have approximately 0.5° × 0.625° spatial resolution ([NASA POWER resolution guidance](https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/); roughly 50–60 km scale near Bangladesh), not field-level measurement. These summaries are displayed next to BRRI sequence examples and do not change their ordering or establish soil-health, yield, or field-suitability outcomes.

### Option B: Local Development (Without Docker)

#### Backend

**Requirements:** Python 3.12, PostgreSQL 16

```bash
cd backend

# Create and activate virtual environment
python3.12 -m venv venv
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# (Optional) Install ML dependencies for disease detection
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements-ml.txt
```

Configure environment:

```bash
cp .env.example .env
# Edit .env:
#   - Set DATABASE_URL to your local PostgreSQL
#   - Set DB_HOST=localhost (not 'db')
#   - Set SECRET_KEY to a random hex string
#   - (Optional) Set GEMINI_API_KEY for AI chat and disease verification
```

Run database migrations and start the server:

```bash
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Seed reference data (crop catalog, agricultural knowledge):

```bash
python -m scripts.import_reference_data
python -m scripts.import_agricultural_knowledge
```

#### Frontend

**Requirements:** Node.js 22+, npm

```bash
cd frontend

# Install dependencies
npm install

# Configure API URL
cp .env.example .env
# Edit .env: set EXPO_PUBLIC_API_URL=http://localhost:8000

# Start development server
npx expo start --port 8082
```

- Press `w` for web browser
- Press `i` for iOS simulator
- Press `a` for Android emulator
- Scan the QR code with Expo Go for physical device

### Option C: Selective Docker Services

```bash
# Backend + Database only (no frontend)
docker compose up backend

# Frontend only (connect to external API)
docker compose up frontend

# Database only
docker compose up db
```

---

## 🔐 Environment Variables

### Root `.env`

| Variable | Required | Description | Default |
|---|---|---|---|
| `DB_USER` | Yes | PostgreSQL username | `fieldshift_user` |
| `DB_PASSWORD` | Yes | PostgreSQL password | `fieldshift_password` |
| `DB_HOST` | Yes | Database host (`db` for Docker, `localhost` for local) | `db` |
| `DB_PORT` | Yes | Database port | `5432` |
| `DB_NAME` | Yes | Database name | `fieldshift_db` |
| `DATABASE_URL` | Yes | Full SQLAlchemy connection string | — |
| `SECRET_KEY` | **Yes** | JWT signing key (must be non-empty) | — |
| `EXPO_PUBLIC_API_URL` | Yes | Backend URL for the frontend | `http://localhost:8000` |

### Backend `.env`

| Variable | Required | Description | Default |
|---|---|---|---|
| `MODULE3_API_BASE_URL` | No | Base URL for Module 3 internal API calls | `http://127.0.0.1:8000` |
| `CORS_ORIGINS` | No | Comma-separated allowed origins | `http://localhost:8082,http://127.0.0.1:8082` |
| `DISEASE_CONFIDENCE_THRESHOLD` | No | Minimum confidence score for disease detection | `0.70` |
| `DISEASE_MODEL_WEIGHTS_PATH` | No | Path to disease model checkpoint | `backend/model/crop_veg_plant_disease_model.pth` |
| `GEMINI_API_KEY` | No | Google Gemini API key (enables AI chat + verification) | — |
| `NASA_POWER_CACHE_DIR` | No | Directory for historical POWER responses; mount persistent storage in deployments | `/tmp/fieldshift-nasa-power-cache` |
| `NASA_POWER_REFRESH_CACHE` | No | Set to `1` to refresh an existing complete-year POWER cache | `0` |
| `GEMINI_MODEL` | No | Gemini model name | `gemini-3.8-flash` |
| `GEMINI_TIMEOUT_SECONDS` | No | Gemini API timeout | `20` |

### Frontend `.env`

| Variable | Required | Description | Default |
|---|---|---|---|
| `EXPO_PUBLIC_API_URL` | Yes | Backend API base URL | `http://localhost:8000` |

> [!NOTE]
> Generate a `SECRET_KEY` with: `python -c "import secrets; print(secrets.token_hex(32))"`

---

## 🗄 Database

### Schema Overview

The database follows the project's six-module architecture with clear ownership boundaries:

```
farmers
│
├── farmer_profiles (M1)
│
└── farmlands (M1)
     │
     ├── farmland_crop_preferences (M2)
     ├── crop_recommendations → crops → crop_varieties (M2)
     │                                   └── agricultural_knowledge
     │
     ├── seasons (M2)
     │     ├── season_plans → growth_stages (M2)
     │     ├── tasks (M3)
     │     ├── problems (M3)
     │     └── farm_checkins (M3)
     │
     ├── weather_events / weather_alerts (M4)
     ├── conversations → chat_messages (M5)
     └── disease_results (M6)
```

### Migrations

Managed by Alembic. Migrations run automatically on Docker startup.

```bash
# Apply all migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"

# View migration history
alembic history
```

### Key Design Decisions

- **UUID primary keys** with `timestamptz` timestamps stored in UTC
- **FarmState is computed**, not persisted — assembled from normalized season, task, problem, and check-in records
- **Task "due" and "overdue" are derived** at query time from `due_at` + current time
- **Season history** replaces a separate `farm_history` table
- **`jsonb` for bounded payloads only** (equipment, observations, reasoning) — not as a replacement for relational data

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific module tests
pytest tests/test_m1_profile_bounds.py
pytest tests/test_m2_advisor.py
pytest tests/test_disease_api.py
pytest tests/test_farm_state_api.py
pytest tests/test_m4_weather_api.py
pytest tests/test_m5_chat.py
```

**Test suites include:**

| Suite | Covers |
|---|---|
| `test_auth_and_farm_resources.py` | Registration, login, farmland CRUD, ownership |
| `test_m1_profile_bounds.py` | Profile field validation and boundary values |
| `test_m1_reference.py` | Location resolution and alias normalization |
| `test_m2_advisor.py` | Crop recommendation engine and suitability logic |
| `test_m2_api.py` | Advisor API endpoints and season lifecycle |
| `test_m2_knowledge.py` | Agricultural knowledge queries |
| `test_m2_contracts.py` | Module 2 shared contract compliance |
| `test_m2_portal_policy.py` | BARC portal policy enforcement |
| `test_m2_source_import.py` | Knowledge source ingestion |
| `test_m2_source_policy.py` | Source acceptance policies |
| `test_m2_numeric_bounds.py` | Numeric field range validation |
| `test_farm_state.py` | Farm state service logic |
| `test_farm_state_api.py` | Module 3 API endpoints |
| `test_farm_state_input_bounds.py` | Task/problem input validation |
| `test_m4_weather_api.py` | Weather assessment and suppression |
| `test_m5_chat.py` | Chat engine and conversation management |
| `test_disease_api.py` | Disease detection pipeline and problem sync |
| `test_bugfixes_regression.py` | Regression tests for resolved bugs |
| `test_local_web_cors.py` | CORS configuration validation |
| `test_reference_ingestion_and_m2_flow.py` | End-to-end reference data ingestion |
| `test_pg_reference_integration.py` | PostgreSQL reference data integration |

### Smoke Test (End-to-End)

```bash
cd backend
python -m scripts.smoke_e2e
```

Runs a full golden-flow scenario: register → create farmland → onboard → recommend crops → select crop → create season → generate plan → import tasks → weather assessment → disease detection.

---

## 🌱 Disease Model Setup

The disease detection feature requires a PyTorch model checkpoint:

1. **Download the model weights** (`crop_veg_plant_disease_model.pth`) — trained ResNet-50 with 94 Bangladesh crop disease classes
2. **Place the file** at `backend/model/crop_veg_plant_disease_model.pth`
3. **Or** set `DISEASE_MODEL_WEIGHTS_PATH` in your environment to a custom path

The class mapping is included at `backend/app/data/plant_disease_classes.json`.

> [!NOTE]
> The disease detection feature gracefully degrades. If the model weights are missing, the endpoint returns a `503` error but the rest of the application works normally.

---

## 📂 Project Structure

```
FieldShiftBD-main/
├── .env.example                    # Root environment template
├── docker-compose.yml              # Three-service Docker stack
├── DB_SCHEMA.md                    # Database schema design document
├── plan.md                         # Project plan & module contracts
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt            # Core Python dependencies
│   ├── requirements-ml.txt         # PyTorch + torchvision (ML)
│   ├── requirements-test.txt       # Test dependencies (pytest)
│   ├── alembic.ini                 # Alembic configuration
│   ├── alembic/
│   │   └── versions/               # Database migration scripts
│   │
│   ├── app/
│   │   ├── main.py                 # FastAPI entry point, middleware, routers
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic settings (env vars)
│   │   │   ├── database.py         # SQLAlchemy engine & session
│   │   │   ├── security.py         # JWT + Argon2 password hashing
│   │   │   └── auth.py             # get_current_farmer_id dependency
│   │   │
│   │   ├── api/                    # Route handlers per module
│   │   │   ├── routes_system.py        # Health check, root
│   │   │   ├── routes_m1_profile.py    # Auth, farmlands, onboarding
│   │   │   ├── routes_m1_catalog.py    # Crop catalog, reference data
│   │   │   ├── routes_m2_advisor.py    # Crop recommendations, seasons
│   │   │   ├── routes_farm_state.py    # Tasks, problems, check-ins (M3)
│   │   │   ├── routes_m4_weather.py    # Weather assessment & alerts
│   │   │   ├── routes_m5_chat.py       # Conversations & messages
│   │   │   └── routes_disease.py       # Disease image analysis (M6)
│   │   │
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── core.py             # Farmer, Farmland, Crop, CropVariety
│   │   │   ├── profile.py          # FarmerProfile
│   │   │   ├── season.py           # Season, SeasonPlan, GrowthStage, CropRecommendation
│   │   │   ├── state.py            # Task, Problem, FarmCheckin
│   │   │   ├── chat.py             # Conversation, ChatMessage
│   │   │   ├── disease.py          # DiseaseResult
│   │   │   └── weather.py          # WeatherEvent, WeatherAlert
│   │   │
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   │   ├── profile.py          # M1 schemas
│   │   │   ├── catalog.py          # Crop catalog schemas
│   │   │   ├── m2_advisor.py       # M2 recommendation/season schemas
│   │   │   ├── farm_state.py       # M3 task/problem/state schemas
│   │   │   ├── weather.py          # M4 weather schemas
│   │   │   ├── chat.py             # M5 chat schemas
│   │   │   └── disease.py          # M6 disease schemas
│   │   │
│   │   ├── services/               # Business logic layer
│   │   │   ├── chat_engine.py          # Intent detection, context grounding, Gemini chat
│   │   │   ├── disease_inference.py    # PyTorch ResNet-50 inference
│   │   │   ├── gemini_verification.py  # Gemini disease verification
│   │   │   ├── farm_state.py           # Farm state computation helpers
│   │   │   ├── farm_state_read_slice.py# Farm state projection for M4
│   │   │   ├── m1_reference.py         # Location resolver, profile vocabulary
│   │   │   ├── m2_advisor.py           # Crop recommendation engine
│   │   │   ├── m2_knowledge.py         # Agricultural knowledge queries
│   │   │   ├── m2_portal_policy.py     # BARC portal data policy
│   │   │   ├── m2_source_policy.py     # Knowledge source policies
│   │   │   ├── m2_source_import.py     # Source data ingestion
│   │   │   ├── mock_farm_state.py      # Golden Farm mock for demos
│   │   │   ├── module3_client.py       # Internal M3 HTTP gateway
│   │   │   ├── weather_providers.py    # Open-Meteo + NASA POWER adapters
│   │   │   ├── weather_suppression.py  # Context-aware alert suppression
│   │   │   └── weather_thresholds.py   # Crop-specific weather thresholds
│   │   │
│   │   └── data/                   # Static data files
│   │       ├── plant_disease_classes.json   # 94-class disease label mapping
│   │       ├── m1_crop_catalog.json         # Crop catalog seed data
│   │       ├── m1_geography_bd.json         # Bangladesh geography reference
│   │       ├── m1_profile_vocabulary.json   # Soil, land type, unit vocabularies
│   │       └── agricultural_knowledge_seed.json  # Initial knowledge base
│   │
│   ├── model/                      # Disease model weights (git-ignored)
│   ├── scripts/                    # Utility scripts
│   │   ├── import_reference_data.py       # Seed crop catalog & geography
│   │   ├── import_agricultural_knowledge.py  # Seed knowledge base
│   │   ├── smoke_e2e.py                   # End-to-end smoke test
│   │   └── probe_routes.py                # Route inspection utility
│   │
│   └── tests/                      # Pytest test suites (21 files)
│
└── frontend/
    ├── Dockerfile
    ├── package.json                # React Native / Expo dependencies
    ├── app.json                    # Expo configuration
    ├── tsconfig.json               # TypeScript configuration
    │
    └── src/
        ├── app/                    # Expo Router screens
        │   ├── index.tsx               # Landing page (bilingual)
        │   ├── _layout.tsx             # Root layout
        │   ├── auth/
        │   │   ├── login.tsx           # Login screen
        │   │   └── signup.tsx          # Registration screen
        │   └── farmlands/
        │       ├── index.tsx           # Redirect
        │       ├── add.tsx             # Create farmland
        │       ├── manage.tsx          # Farmland list
        │       ├── profile-setup.tsx   # Guided onboarding flow
        │       └── [id]/
        │           ├── _layout.tsx         # Farmland layout + navigation
        │           ├── index.tsx           # Dashboard overview
        │           ├── tasks.tsx           # Task management
        │           ├── problems.tsx        # Problem tracking
        │           ├── check-ins.tsx       # Check-in recording
        │           ├── crop-advisor.tsx     # Crop recommendations
        │           ├── season-plan.tsx      # Season plan viewer
        │           ├── crop-health.tsx      # Disease detection (scan leaf)
        │           ├── alerts.tsx           # Weather alerts
        │           ├── chat.tsx             # AI conversation
        │           └── resources.tsx        # Agricultural resources
        │
        ├── components/             # Reusable UI components
        │   ├── FarmlandChat.tsx         # Chat interface
        │   ├── ScanLeafResult.tsx       # Disease scan result display
        │   ├── CropAdvisorPresentation.tsx  # Recommendation cards
        │   ├── FarmlandSidebar.tsx      # Navigation sidebar
        │   ├── OptionPickerModal.tsx    # Selection modal
        │   └── *-icons.tsx             # SVG icon components
        │
        ├── context/
        │   └── AppProvider.tsx     # Global state (auth, farmlands, user)
        │
        ├── services/               # API communication layer
        │   ├── api-client.ts           # Authenticated HTTP client
        │   ├── farm-data.ts            # Farm state data fetching
        │   ├── farm-location.ts        # GPS location services
        │   ├── language.ts             # Language preference storage
        │   ├── m1-reference.ts         # Reference data client
        │   ├── m2-advisor.ts           # Crop advisor client
        │   └── m5-chat.ts             # Chat API client
        │
        └── theme/                  # Design tokens and styling
```

---

## 📜 Scripts Reference

| Script | Description |
|---|---|
| `scripts/import_reference_data.py` | Seeds the crop catalog, crop varieties, and Bangladesh geography data into the database |
| `scripts/import_agricultural_knowledge.py` | Imports BARC-sourced agricultural knowledge records |
| `scripts/import_m2_barc_evidence.py` | Imports BARC portal evidence data |
| `scripts/capture_barc_portal_sources.py` | Captures source data from BARC portals |
| `scripts/smoke_e2e.py` | Full end-to-end smoke test (register → disease detection) |
| `scripts/probe_routes.py` | Inspect registered FastAPI routes |
| `scripts/inspect_knowledge.py` | Query and inspect agricultural knowledge records |

---

## 🤝 Contributing

### Module Ownership Rules

1. **Single owner per data domain** — each module owns its data; others may read but must not create competing sources of truth
2. **Suggestions allowed only inside your module** — better algorithms, UX, testing strategies within scope
3. **No cross-module changes without team agreement** — shared contracts, dependencies, and data ownership are team-level decisions
4. **Contract-first development** — all modules build against agreed shared contracts with mock data support

### Development Workflow

```bash
# Run backend with hot reload
cd backend && uvicorn app.main:app --reload

# Run frontend with hot reload
cd frontend && npx expo start --port 8082

# Run tests
cd backend && pytest -v

# Create a new migration after model changes
cd backend && alembic revision --autogenerate -m "description"
```

---

## 📄 License

MIT License — see [LICENSE](frontend/LICENSE) for details.
