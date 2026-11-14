<p align="center">
  <img src="frontend/assets/images/icon.png" alt="FieldShift BD" width="96" />
</p>

<h1 align="center">FieldShift BD</h1>

<p align="center">
  <strong>NASA farm data, in a farmer's own language.</strong><br>
  A Bangla and English farm helper that helps farmers in Bangladesh decide what to grow next, and when.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/NASA%20Space%20Apps-2026-0B3D91" alt="NASA Space Apps 2026" />
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/Expo-SDK%2057-000020?logo=expo&logoColor=white" alt="Expo SDK 57" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL 16" />
  <img src="https://img.shields.io/badge/License-Apache--2.0-green" alt="Apache-2.0" />
</p>

<p align="center">
  <a href="#what-it-does">What it does</a> ·
  <a href="#nasa-data">NASA data</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="ARCHITECTURE.md">Architecture</a> ·
  <a href="API_DOCUMENTATION.md">API</a> ·
  <a href="AI_DISCLOSURE.md">AI disclosure</a> ·
  <a href="#team">Team</a>
</p>

---

Built by **Team Zero Requiem** (Chittagong, Bangladesh) for the NASA Space Apps Challenge 2026 challenge **[Field Shift: Adapting Farms with NASA Data](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/)**.

> FieldShift BD is an independent project. NASA does not endorse it. It supports farmer and local expert judgment; it never replaces it.

## The problem

Nearly half of Bangladesh's workers depend on farming (BBS Labour Force Survey 2022), and they plan each season around rain they cannot predict. NASA POWER data for Rajshahi shows yearly rainfall swinging from **1,015 mm (2012) to 2,080 mm (2020)**, and usable monsoon rain starting anywhere from **1 April to 2 May**. From November to March almost no rain falls, so dry-season crops such as Boro rice depend on pumped groundwater.

NASA has recorded this every day for decades, but the data sits in English websites and spreadsheets, far from a farmer's phone.

## What it does

| Feature | What the farmer gets |
| --- | --- |
| **Field profile with a map** | Save the field's district, location, soil, land type, water source and last crop. A Bangladesh district map shows where the field is. |
| **Crop Advisor** | Crops whose published BARC land and soil conditions match the saved field, with the source and its review date. |
| **Rotation comparison** | The farmer's current crops compared with three BRRI-published rotations. The farmer picks a priority (less irrigation water, fewer dry spells, crop variety, published dates) and the options re-order. Each option shows why it is shown, possible benefits, risks to check locally and what is still unknown. |
| **"Where the NASA data comes from"** | The field, the NASA POWER reference point and its 55 × 63 km grid cell on a map, with a plain note that the data describes the area, not one plot. |
| **Season plan and harvest window** | Seedbed, transplanting and harvest windows from published BRRI variety calendars. |
| **Weather alerts and tasks** | Alerts for heavy rain, heat and wind from the 7-day forecast and the last 30 days of NASA POWER, plus field reminders such as checking soil moisture before irrigating. |
| **Leaf health check** | A leaf photo screened by an AI model for 94 crop conditions. It says when it is unsure and points the farmer to a local agriculture officer. |
| **Ask in Bangla** | A farm-aware chat. The farmer can speak a question in Bangla and hear the answer read aloud. Messages queue while offline. |
| **Public district rainfall** | Rainfall history and published crop calendars by district, no account needed. |

Everything is available in Bangla and English.

## NASA data

| Dataset | How FieldShift BD uses it |
| --- | --- |
| [NASA POWER Daily Point](https://power.larc.nasa.gov/docs/services/api/temporal/daily/): precipitation, temperature, solar radiation | Cached 2001–2025 daily records for the Rajshahi, Chattogram and Dhaka reference points drive the rainfall-onset and dry-spell analysis, the "fewer dry spells" ranking in the rotation comparison and the public district advisory. The last 30 days at the farm's coordinates feed the weather alerts. |
| [GPM IMERG Final Daily V07](https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGDF_07/summary) | A one-day pilot sample shown as context next to the field. Not used in ranking yet. |
| [SRTM GL1 v003](https://lpdaac.usgs.gov/products/srtmgl1v003/) | Elevation at the farm's location, shown as context. |
| [NASA Earthdata CMR](https://cmr.earthdata.nasa.gov/search/) | Finding IMERG and SRTM granules for the pilot districts. |

The NASA POWER grid is 0.5° × 0.625°. Caches carry manifests with coverage, retrieval time and SHA-256 hashes so results can be reproduced. Other sources (BRRI, BARC, Open-Meteo, geoBoundaries, BBS) are listed in [ARCHITECTURE.md](ARCHITECTURE.md#data-and-evidence).

## How it fits the challenge

| Challenge asks for | FieldShift BD today | Still to do |
| --- | --- | --- |
| NASA Earth observations | NASA POWER drives rainfall onset, dry spells and the rotation order; IMERG and SRTM shown as context | Bring IMERG into the analysis; add SMAP soil moisture |
| Local soil information | Saved soil texture, land type, irrigation and water source decide which published rotations apply | Calibrated soil data rather than farmer-entered values |
| Crop characteristics | BRRI rotations and variety calendars, BARC crop zoning, crop families and dry-season water use | Agronomist-reviewed turnaround and water-demand rules |
| Farmer priorities | The chosen priority re-orders the options using values shown on screen | Market and income data |
| Compare rotation strategies, including the current one | The farmer's current crops plus three BRRI rotations | More patterns beyond the irrigated high-land ecosystem |
| Show reasons, evidence, benefits, gaps and risks | Every option lists all five, in Bangla and English | Measured benefits from field trials |

Rotation comparison currently covers **Rajshahi** and **Chattogram**. No option is ever selected for the farmer.

## Quick start

### Requirements

- Git and [Git LFS](https://git-lfs.com/) (for the disease model checkpoint)
- Docker Desktop with Docker Compose

```bash
git clone https://github.com/aroyy007/FieldShiftBD.git
cd FieldShiftBD
git lfs install
git lfs pull
```

### Configure

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

Set `SECRET_KEY` in `backend/.env` to a random value of at least 32 characters; the API refuses to start without it.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Optional: `GEMINI_API_KEY` turns on chat answers and the scan double-check. Other settings are described in [API_DOCUMENTATION.md](API_DOCUMENTATION.md#feature-switches).

### Run

```bash
docker compose up --build
```

| Service | Address |
| --- | --- |
| App (Expo web) | <http://localhost:8082> |
| API | <http://localhost:8000> |
| Interactive API docs | <http://localhost:8000/docs> |
| Health check | <http://localhost:8000/health> |

On every start the backend applies database migrations and imports the bundled crop catalog and BARC/BRRI knowledge (about 5 seconds).

Stop with `Ctrl+C` or `docker compose down`; `docker compose down -v` also deletes the database volume.

For Android or iOS development, run `npm ci` and `npm start` in `frontend/` and set `EXPO_PUBLIC_API_URL` to an address the phone can reach (a phone cannot use its own `localhost`).

> **macOS and iCloud Drive:** keep the project folder fully downloaded (Finder → right-click → **Keep Downloaded**). Docker cannot read cloud-only placeholder files and the backend fails with `OSError: [Errno 5] Input/output error`.

## Tests

```bash
# backend (Python 3.12)
cd backend
python -m pip install -r requirements.txt -r requirements-test.txt
python -m pytest -q

# frontend
cd frontend
npx tsc --noEmit && npm run lint && npm test
```

CI runs contract checks, each module's tests and a PostgreSQL integration job on every push. See [ARCHITECTURE.md](ARCHITECTURE.md#testing-and-ci).

## Documentation

| Document | Contents |
| --- | --- |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, the six backend modules, how a rotation comparison is built, data sources, frontend structure, security |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Every API route, authentication, errors, request and response shapes, examples |
| [AI_DISCLOSURE.md](AI_DISCLOSURE.md) | AI tools used in development, in the app and in our videos |
| [`docs/plans/`](docs/plans/) | Project plan, module briefs, team roadmap |
| [`docs/research/`](docs/research/), [`docs/reviews/`](docs/reviews/) | Dated source research and verification records |
| [`backend/model/README.md`](backend/model/README.md) | Disease model card, licence and limits |

## Project map

| Path | Purpose |
| --- | --- |
| `frontend/src/app/` | Expo Router screens |
| `frontend/src/components/` | Shared UI, including the rotation panel and field map |
| `frontend/src/services/` | API client, voice, offline queue |
| `backend/app/api/` | FastAPI routes |
| `backend/app/services/` | Domain logic and data providers |
| `backend/app/contracts/` | Typed contracts shared with the frontend |
| `backend/src/compute/` | Deterministic climate and rotation calculations |
| `backend/data/climate/` | NASA POWER caches and source register |
| `backend/data/earth_observation/` | IMERG and SRTM pilot samples |
| `backend/app/data/` | BRRI and BARC source captures, crop catalog, geography |
| `backend/tests/` | API, domain, contract and data tests |

## Limitations

- Rotation comparison supports Rajshahi and Chattogram; NASA POWER caches exist for Rajshahi, Chattogram and Dhaka.
- NASA POWER describes a 55 × 63 km grid cell, not a single field.
- Rotation benefits are qualitative general agronomy, not measured yield, profit or soil change.
- Weather alert thresholds are demo values pending agronomist review.
- The disease model's accuracy comes from its upstream model card and has not been validated on Bangladeshi field photos. It is a screening tool, not a diagnosis.
- Bangla voice input depends on the phone or browser supporting `bn-BD` speech recognition.

## Team

**Team Zero Requiem**, Chittagong, Bangladesh

| Name | Role |
| --- | --- |
| Arijit Roy | Team lead · Computer vision |
| Atri Mazumder Arka | System design & conversational AI |
| Aveshek Singha | Full stack & integration |
| Israt Jahan | Crop & climate data |
| Shahriar Khaled Fahim | AI & farm intelligence |
| Shariful Islam | Earth observation & weather |

## Licence and attribution

Source code and documentation are licensed under [Apache-2.0](LICENSE). Third-party assets keep their own terms; see [`NOTICE`](NOTICE):

- Disease model checkpoint: Saon110, CC BY-NC 4.0 (non-commercial)
- NASA POWER, GPM IMERG, SRTM: NASA open data (use does not imply NASA endorsement)
- BARC Agri-Advisory Portal and BRRI publications: reproduced with source acknowledgement
- District boundaries: geoBoundaries (BBS, OCHA ROAP), CC BY 3.0 IGO
