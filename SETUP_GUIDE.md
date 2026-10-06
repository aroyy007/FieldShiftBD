# FieldShift Setup Guide

## 1. Clone the Repository

```bash
git clone <REPOSITORY_URL>
cd "Project - FieldShift"
```

## 2. Create the `.env` File

At the project root, there is an `.env.example` file.

Copy it to `.env`:

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### Linux / macOS

```bash
cp .env.example .env
```

Update the `.env` values if necessary.

## 3. Start the Entire Project

Make sure Docker Desktop is running, then:

```bash
docker compose up -d
```

This starts:

- `backend`
- `frontend`
- `db`

## 4. Start Only the Backend

If you only need the backend:

```bash
docker compose up -d backend
```

The `db` service will also start automatically because the backend depends on it.

## 5. Start Backend + Database

```bash
docker compose up -d backend db
```

## 6. Start Only the Frontend

```bash
docker compose up -d frontend
```

## 7. Check Running Services

```bash
docker compose ps
```

That's it. 🚀
