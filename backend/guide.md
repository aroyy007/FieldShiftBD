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
├── docker-compose.yml   → Runs BOTH the FastAPI server AND the PostgreSQL database
├── .dockerignore        → Files to exclude from the Docker image (venv, .env, etc.)
├── .env                 → YOUR local secrets/credentials (you create this, never commit it)
├── .env.example         → Template for the .env file (safe to commit, already in git)
├── requirements.txt     → List of all Python packages the project needs
│
├── alembic.ini          → Alembic configuration (do not edit this)
├── alembic/
│   ├── env.py           → Wires Alembic to our database settings (do not edit this)
│   └── versions/        → Migration files that create/modify DB tables
│                           ⚠️ NEVER delete or edit files here manually.
│                           ⚠️ Always commit new migration files to git.
│
└── app/
    ├── main.py          → FastAPI app entry point (registers all routes)
    ├── core/
    │   ├── config.py    → Reads .env variables (DB credentials etc.)
    │   └── database.py  → Creates the DB connection and session
    ├── models/          → SQLAlchemy models = the actual database tables in Python
    │   ├── core.py      → Tables: farmers, farmlands, crops
    │   ├── profile.py   → Module 1 tables: farmer_profiles, farm_history
    │   ├── season.py    → Module 2 tables: seasons, season_plans, growth_stages
    │   ├── state.py     → Module 3 tables: farm_states, tasks, problems, checkins
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

All commands in this guide must be run inside the `backend/` folder.
You can use the **integrated terminal of your IDE** (VS Code, PyCharm, etc.) or any standalone terminal (macOS Terminal, Windows PowerShell, Windows Terminal).

**Open your terminal and navigate to the backend folder first:**

**macOS / Linux:**
```bash
cd path/to/FieldShiftBD/backend
```

**Windows (PowerShell):**
```powershell
cd path\to\FieldShiftBD\backend
```

> ✅ All commands from this point forward assume your terminal is already inside `backend/`.

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

> ✅ The default values in `.env.example` already match the Docker settings. You do **not** need to change anything unless you have a specific reason to.

---

### Step 3 — Build and Start Everything

This one command builds the FastAPI Docker image, starts the API server, and starts the PostgreSQL database — all at once:

```bash
docker-compose up --build
```

> ✅ The **first time** you run this, it downloads the Python and Postgres Docker images. This may take 1-2 minutes depending on your internet speed. Every time after that it will be instant.
>
> ✅ The `--build` flag rebuilds the image if anything has changed. You only need it the first time or after changing `requirements.txt`. After that you can just use `docker-compose up`.

Wait until you see this line in the output:
```
fieldshift_api  | INFO:     Application startup complete.
```

The backend is now fully running! Open your browser and visit:
- **API:** `http://localhost:8000`
- **Swagger Docs:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`

---

### Step 4 — Run Database Migrations (First Time Only)

After the containers are running, open a **new terminal tab** (keep the first one running), navigate to the `backend/` folder, and run:

```bash
docker-compose exec api alembic upgrade head
```

> ✅ This runs the Alembic migration command **inside the `api` container** against the real database. It sets up all the required tables.
>
> ✅ Running this even when there is nothing to migrate is completely safe — it simply does nothing.

---

## 🔁 Part 2: Every Day Workflow

> Do these steps **every time** you start working on the backend.

---

### Step 1 — Open Docker Desktop

Make sure Docker Desktop is open and running before proceeding.

---

### Step 2 — Start All Containers

```bash
docker-compose up
```

> ✅ Notice there is no `--build` this time. You only need `--build` the very first time or after updating `requirements.txt`.
>
> ✅ The FastAPI server has **hot-reload** enabled. When you save any `.py` file, the server automatically restarts inside the container. You will see the reload in the terminal output. No need to stop and restart anything.

To stop everything when you are done for the day, press `Ctrl + C` in the terminal.

Or to stop and remove the containers:
```bash
docker-compose down
```

---

### Step 3 — Pull Latest Code and Apply Migrations

After pulling new code from a teammate:
```bash
git pull
docker-compose exec api alembic upgrade head
```

> ✅ Always run `alembic upgrade head` after pulling. It applies any new migration files your teammates may have pushed.

---

## ⚙️ Part 3: When You Change the Database Schema

If you add a new table or add/remove a column in any file inside `app/models/`, you **must** create a migration and commit it so your teammates' databases also get updated.

**Step 1 — Generate the migration file automatically:**
```bash
docker-compose exec api alembic revision --autogenerate -m "describe what you changed"
```
Example:
```bash
docker-compose exec api alembic revision --autogenerate -m "added crop variety field to seasons"
```

**Step 2 — Apply the migration to your local database:**
```bash
docker-compose exec api alembic upgrade head
```

**Step 3 — Commit the new migration file:**
```bash
git add alembic/versions/
git commit -m "migration: added crop variety field to seasons"
git push
```

> ⚠️ **Important:** Always commit your migration files. Your teammates will run `alembic upgrade head` after pulling your code and their databases will be updated automatically. Never delete or manually edit files inside `alembic/versions/`.

---

## 📦 Part 4: When You Install a New Package

If you need to add a new Python package:

1. Add it to `requirements.txt` manually (with a pinned version).
2. Rebuild the Docker image so the new package is installed inside the container:
   ```bash
   docker-compose up --build
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
| Start everything (first time) | `docker-compose up --build` |
| Start everything (daily) | `docker-compose up` |
| Stop everything | `Ctrl + C` or `docker-compose down` |
| Apply DB migrations | `docker-compose exec api alembic upgrade head` |
| Generate new migration | `docker-compose exec api alembic revision --autogenerate -m "msg"` |
| Check current DB version | `docker-compose exec api alembic current` |
| See migration history | `docker-compose exec api alembic history` |
| Open a shell inside the api container | `docker-compose exec api bash` |
| List all databases in Postgres | `docker exec -it fieldshift_pg psql -U fieldshift_user -d fieldshift_db -c "\l"` |

---

## 🚨 Common Issues

**`Cannot connect to the Docker daemon`**
→ Docker Desktop is not running. Open it and wait for it to fully start, then try again.

**`port is already allocated`**
→ Something else on your machine is using port `8000` or `5433`. Stop that process or change the port in `docker-compose.yml`.

**`ModuleNotFoundError: No module named 'xxx'`**
→ You added a package but didn't rebuild. Run `docker-compose up --build`.

**`psycopg2.OperationalError: could not connect to server`**
→ The `db` container is not healthy yet. Wait a few seconds and try again. If it persists, run `docker-compose down` then `docker-compose up`.

**`alembic.util.exc.CommandError: Target database is not up to date.`**
→ Run `docker-compose exec api alembic upgrade head` to apply pending migrations.

**`Error: .env file not found`**
→ You have not created your `.env` file yet. Run `cp .env.example .env` (Mac) or `copy .env.example .env` (Windows).
