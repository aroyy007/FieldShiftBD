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
├── docker-compose.yml   → Runs our PostgreSQL database inside Docker
├── .env                 → YOUR local secrets/credentials (you create this, never commit it)
├── .env.example         → Template for the .env file (safe to commit, already in git)
├── .python-version      → Tells pyenv to use Python 3.12.3 in this folder
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
        ├── dependencies.py           → Shared dependencies (DB session, auth)
        ├── routes_m1_profile.py      → /profile/* endpoints
        ├── routes_m2_advisor.py      → /advisor/* endpoints
        ├── routes_m3_farm_brain.py   → /farm-brain/* endpoints
        ├── routes_m4_weather.py      → /weather/* endpoints
        ├── routes_m5_chat.py         → /chat/* endpoints
        └── routes_m6_disease.py      → /disease/* endpoints
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

Docker is used to run the PostgreSQL database on your machine without installing Postgres directly.

- Download and install Docker Desktop from: https://www.docker.com/products/docker-desktop/
- After installing, **open Docker Desktop** and leave it running in the background.
- Verify it works by running this in your terminal:
  ```bash
  docker --version
  ```
  You should see something like `Docker version 26.x.x`.

---

### Step 2 — Install Python 3.12.3

We all use **the exact same Python version** to avoid compatibility issues.

**On macOS (using pyenv — recommended):**
```bash
# Install pyenv (skip if already installed)
brew install pyenv

# Add pyenv to your shell (for zsh, the default on macOS)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# Install the required Python version
pyenv install 3.12.3
```
> ✅ Once done, pyenv will automatically switch to Python 3.12.3 whenever you `cd` into the `backend/` folder, because of the `.python-version` file already there.

**On Windows (using pyenv-win):**
```powershell
# Install pyenv-win (run in PowerShell as Administrator)
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"

# Close and reopen PowerShell, then run:
pyenv install 3.12.3
pyenv global 3.12.3
```
> ⚠️ If you get an Execution Policy error, first run:
> `Set-ExecutionPolicy Unrestricted -Scope CurrentUser`

---

### Step 3 — Create a Virtual Environment

A virtual environment keeps the project's Python packages isolated from the rest of your machine.

> ⚠️ Make sure you are inside the `backend/` folder before running these commands.

**On macOS / Linux:**
```bash
python3 -m venv venv
```

**On Windows (PowerShell):**
```powershell
python -m venv venv
```

---

### Step 4 — Activate the Virtual Environment

You must activate the virtual environment to use it. **You will do this every day**, but you need to create it only once (Step 3 above).

**On macOS / Linux:**
```bash
source venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate
```

> ✅ When active, you will see `(venv)` at the start of your terminal prompt, like:
> `(venv) fahim@MacBook backend %`

---

### Step 5 — Install Python Packages

With the virtual environment **activated**, install all required packages:

```bash
pip install -r requirements.txt
```

> ✅ This reads `requirements.txt` and installs the exact package versions the project needs (FastAPI, SQLAlchemy, Alembic, etc.).

---

### Step 6 — Create Your `.env` File

The `.env` file holds your local database credentials. It is **never committed to git** to keep secrets safe.

**On macOS / Linux:**
```bash
cp .env.example .env
```

**On Windows (PowerShell):**
```powershell
copy .env.example .env
```

> ✅ The default values in `.env.example` already match the Docker database settings, so you do **not** need to change anything in the file unless you customised your Docker setup.

---

## 🔁 Part 2: Every Day Workflow

> Do these steps **every time** you start working on the backend.

---

### Step 1 — Start Docker Desktop

Open Docker Desktop from your Applications (macOS) or Start Menu (Windows) and wait for it to fully load.

---

### Step 2 — Start the Database Container

This starts the PostgreSQL database in the background:

```bash
docker-compose up -d
```

> ✅ The `-d` flag means it runs in the background so your terminal stays free.
> You will see: `Container fieldshift_pg  Started`

To stop the database when you are done for the day:
```bash
docker-compose down
```

---

### Step 3 — Activate Your Virtual Environment

**On macOS / Linux:**
```bash
source venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate
```

---

### Step 4 — Pull Latest Code and Run Migrations

After pulling new code from git, always run:
```bash
git pull
alembic upgrade head
```

> ✅ `alembic upgrade head` checks the `alembic/versions/` folder for any new migration files that a teammate may have pushed and applies those changes to your local database. Running it even when there is nothing new is completely safe — it simply does nothing.

---

### Step 5 — Start the FastAPI Server

```bash
uvicorn app.main:app --reload
```

> ✅ `--reload` means the server automatically restarts whenever you save a Python file. This is your development mode flag.

The server runs at:
- **API Base URL:** `http://127.0.0.1:8000`
- **Swagger Docs (interactive API explorer):** `http://127.0.0.1:8000/docs`
- **ReDoc Docs:** `http://127.0.0.1:8000/redoc`

---

## ⚙️ Part 3: When You Change the Database Schema

If you add a new table or add/remove a column in any file inside `app/models/`, you **must** create a migration and commit it so your teammates' databases also get updated.

**Step 1 — Generate the migration file automatically:**
```bash
alembic revision --autogenerate -m "describe what you changed here"
```
Example:
```bash
alembic revision --autogenerate -m "added crop variety field to seasons"
```

**Step 2 — Apply the migration to your local database:**
```bash
alembic upgrade head
```

**Step 3 — Commit the new migration file:**
```bash
git add alembic/versions/
git commit -m "migration: added crop variety field to seasons"
git push
```

> ⚠️ **Important:** Always commit your migration files. Your teammates will run `alembic upgrade head` after pulling your code and their databases will be updated automatically. Never delete or manually edit files inside `alembic/versions/`.

---

## ❓ Quick Reference

| Task | Command |
|---|---|
| Activate venv (Mac) | `source venv/bin/activate` |
| Activate venv (Windows) | `.\venv\Scripts\Activate` |
| Start DB | `docker-compose up -d` |
| Stop DB | `docker-compose down` |
| Apply DB migrations | `alembic upgrade head` |
| Start dev server | `uvicorn app.main:app --reload` |
| Install new packages | `pip install <package>` then update `requirements.txt` |
| Generate migration | `alembic revision --autogenerate -m "message"` |
| Check current DB version | `alembic current` |
| See migration history | `alembic history` |

---

## 🚨 Common Issues

**`ModuleNotFoundError: No module named 'fastapi'`**
→ Your virtual environment is not activated. Run `source venv/bin/activate` (Mac) or `.\venv\Scripts\Activate` (Windows).

**`psycopg2.OperationalError: could not connect to server`**
→ The database container is not running. Run `docker-compose up -d` and try again.

**`alembic.util.exc.CommandError: Target database is not up to date.`**
→ Run `alembic upgrade head` to apply pending migrations.

**`Error: .env file not found`**
→ You have not created your `.env` file yet. Run `cp .env.example .env` (Mac) or `copy .env.example .env` (Windows).
