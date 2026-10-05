# FieldShift Backend — Developer Guide

> Read this entire guide once before you start. It will save you a lot of confusion later.

---

> **🤖 Note for AI Agents:**
> This file explains the folder structure and setup commands for the backend only.
> Before writing any code, you **must** also read these two files at the root of the repository:
> - `plan.md` — The 6-module architecture, what each module owns, and strict ownership rules.
> - `fieldshift-database-schema.md` — Every database table, every field, and the relationships between them.
>
> Without reading those two files first, you will not have enough context to write correct code for this project.

---

## 📁 What Each Folder Does

```text
backend/
├── Dockerfile           → Instructions to build the FastAPI backend Docker image
├── .dockerignore        → Files to exclude from the Docker image (venv, .env, etc.)
├── requirements.txt     → List of all Python packages the project needs
│
├── alembic.ini          → Alembic configuration (do not edit this)
├── alembic/
│   ├── env.py           → Wires Alembic to our database settings (do not edit this)
│   └── versions/        → Versioned migration files that create/modify DB tables
│                           ⚠️ Commit reviewed migration files with model changes.
│
└── app/
    ├── main.py          → FastAPI app entry point (registers all routes)
    ├── core/
    │   ├── config.py    → Reads .env variables (DB credentials etc.)
    │   └── database.py  → Creates the DB connection and session
    ├── models/          → SQLAlchemy models = the actual database tables in Python
    │   ├── core.py      → Tables: farmers, farmlands, crops
    │   ├── profile.py      → Module 1 tables: farmer_profiles
    │   ├── season.py    → Module 2 tables: seasons, season_plans, growth_stages
    │   ├── state.py        → Module 3 tables: tasks, problems, checkins
    │   ├── weather.py   → Module 4 tables: weather_events, weather_alerts
    │   ├── chat.py      → Module 5 tables: conversations, chat_messages
    │   └── disease.py   → Module 6 tables: disease_results
    ├── schemas/         → Pydantic models = validates API request/response JSON
    ├── services/        → Business logic (calculations, AI calls, etc.)
    └── api/             → HTTP routes (what URLs the API exposes)
        ├── routes_system.py              → /health endpoint
        ├── routes_m1_profile.py          → /profile/* endpoints
        ├── routes_m2_advisor.py          → /advisor/* endpoints
        ├── routes_m3_farm_brain.py       → /farm-brain/* endpoints
        ├── routes_m4_weather.py          → /weather/* endpoints
        ├── routes_m5_chat.py             → /chat/* endpoints
        └── routes_m6_disease.py          → /disease/* endpoints
```

---

## ⚠️ Before You Run Any Command

Run Docker Compose commands from the repository root, where the shared
`docker-compose.yml` and `.env` file live. Run Python/Alembic commands inside
the API container as shown below.
You can use the **integrated terminal of your IDE** (VS Code, PyCharm, etc.) or any standalone terminal (macOS Terminal, Windows PowerShell, Windows Terminal).

**Open your terminal and navigate to the repository root first:**

**macOS / Linux:**
```bash
cd path/to/FieldShiftBD
```

**Windows (PowerShell):**
```powershell
cd path\to\FieldShiftBD
```

> ✅ All commands from this point forward assume your terminal is already at the repository root.

---

## 🛠️ Part 1: One-Time Setup

> Do these steps **only once** when you first clone the project.
> You do **not** need to repeat these steps every day.

---

### Step 1 — Install Docker Desktop

Docker is the **only tool you need to install** to run the entire backend (the FastAPI server AND the database). No Python installation, no virtual environments, no pyenv.

- Download and install Docker Desktop from: https://www.docker.com/products/docker-desktop/
- After installing, **open Docker Desktop** and leave it running in the background whenever you are coding.
- Verify it works:
  ```bash
  docker --version
  ```
  You should see something like `Docker version 26.x.x`.

---

### Step 2 — Create Your `.env` File

The `.env` file holds your local database credentials. It is **never committed to git** to keep secrets safe.

**On macOS / Linux:**
```bash
cp .env.example .env
```

**On Windows (PowerShell):**
```powershell
copy .env.example .env
```

> ✅ The root `.env.example` supplies matching settings to PostgreSQL and the API. It is for local development only; change credentials in your local `.env` if needed.

---

### Step 3 — Build and Start Everything

This one command builds and starts the FastAPI backend, PostgreSQL database, and Expo web frontend:

```bash
docker compose up --build
```

> ✅ The **first time** you run this, it downloads the Python and Postgres Docker images. This may take 1-2 minutes depending on your internet speed. Every time after that it will be instant.
>
> ✅ The `--build` flag builds both app images. Use it the first time and after changing `backend/requirements.txt`, either Dockerfile, or frontend dependencies. Otherwise use `docker compose up`.

Wait until you see this line in the output:
```
api-1  | INFO:     Application startup complete.
```

The backend is now fully running! Open your browser and visit:
- **Frontend (Expo web):** `http://localhost:8082`
- **API:** `http://localhost:8000`
- **Swagger Docs:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`

---

### Step 4 — Verify the Database Connection

The API container runs `alembic upgrade head` before starting FastAPI. On first startup,
the committed initial migration creates all tables. On later startups, Alembic applies
new committed migrations and preserves existing data. If migration fails, the API does
not start.

Check `http://localhost:8000/health`. A healthy response includes
`"database": "connected"`.

---

## 🔁 Part 2: Every Day Workflow

> Do these steps **every time** you start working on the backend.

---

### Step 1 — Open Docker Desktop

Make sure Docker Desktop is open and running before proceeding.

---

### Step 2 — Start All Containers

```bash
docker compose up
```

> ✅ Notice there is no `--build` this time. Rebuild after changing backend/frontend dependencies or either Dockerfile.
>
> ✅ The FastAPI server has **hot-reload** enabled. When you save any `.py` file, the server automatically restarts inside the container. You will see the reload in the terminal output. No need to stop and restart anything.

To stop everything when you are done for the day, press `Ctrl + C` in the terminal.

Or to stop and remove the containers:
```bash
docker compose down
```

---

### Step 3 — Pull Latest Code and Apply Migrations

After pulling new code from a teammate:
```bash
git pull
docker compose restart api
```

> ✅ The API runs `alembic upgrade head` at startup. If dependencies or a Dockerfile changed, rebuild with `docker compose up --build`.

---

## ⚙️ Part 3: When You Change the Database Schema

If you add a new table or add/remove a column in any file inside `app/models/`, you **must** create a migration and commit it so your teammates' databases also get updated.

**Step 1 — Generate the migration file automatically:**
```bash
docker compose exec api alembic revision --autogenerate -m "describe what you changed"
```
Example:
```bash
docker compose exec api alembic revision --autogenerate -m "added crop variety field to seasons"
```

**Step 2 — Apply the migration to your local database:**
```bash
docker compose exec api alembic upgrade head
```

**Step 3 — Commit the new migration file:**
```bash
git add alembic/versions/
git commit -m "migration: added crop variety field to seasons"
git push
```

> ⚠️ **Important:** Commit reviewed migration files with model changes. Teammates' API containers apply them at startup. Never delete a migration that has already been applied to a shared database.

---

## 📦 Part 4: When You Install a New Package

If you need to add a new Python package:

1. Add it to `requirements.txt` manually (with a pinned version).
2. Rebuild the Docker image so the new package is installed inside the container:
   ```bash
   docker compose up --build
   ```
3. Commit the updated `requirements.txt`:
   ```bash
   git add requirements.txt
   git commit -m "chore: added <package-name> to requirements"
   ```

> ✅ Do **NOT** run `pip install` directly. Since everything runs inside Docker, the package must be added to `requirements.txt` and the image must be rebuilt so all teammates get it automatically.

---

## ❓ Quick Reference

| Task | Command |
|---|---|
| Start everything (first time) | `docker compose up --build` |
| Start everything (daily) | `docker compose up` |
| Stop everything | `Ctrl + C` or `docker compose down` |
| Apply DB migrations manually | `docker compose exec api alembic upgrade head` |
| Generate new migration | `docker compose exec api alembic revision --autogenerate -m "msg"` |
| Check current DB version | `docker compose exec api alembic current` |
| See migration history | `docker compose exec api alembic history` |
| Open a shell inside the API container | `docker compose exec api sh` |
| List databases in Postgres | `docker compose exec db psql -U fieldshift_user -d fieldshift_db -c "\l"` |

---

## 🚨 Common Issues

**`Cannot connect to the Docker daemon`**
→ Docker Desktop is not running. Open it and wait for it to fully start, then try again.

**`port is already allocated`**
→ Something else on your machine is using port `8000`, `8082`, or `5433`. Stop that process or change the corresponding port in the root `docker-compose.yml`.

**`ModuleNotFoundError: No module named 'xxx'`**
→ You added a package but didn't rebuild. Run `docker compose up --build`.

**`psycopg2.OperationalError: could not connect to server`**
→ The `db` container is not healthy yet. Wait a few seconds and try again. If it persists, run `docker compose down` then `docker compose up`.

**`alembic.util.exc.CommandError: Target database is not up to date.`**
→ The API applies committed migrations at startup. Check `docker compose logs api`; restart with `docker compose restart api`. For a manual retry, run `docker compose exec api alembic upgrade head`.

**`Error: .env file not found`**
→ You have not created your `.env` file yet. Run `cp .env.example .env` (Mac) or `copy .env.example .env` (Windows).
