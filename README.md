# FieldShift

## Run the full development stack

Install Docker Desktop, then from the repository root create your local environment
file and build/start the database, API, and Expo web app:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open:

- Frontend (Expo web): http://localhost:8082
- Backend API: http://localhost:8000
- Backend API docs: http://localhost:8000/docs
- Backend/database health: http://localhost:8000/health

After the first build, start the stack with `docker compose up`. Stop it with
`Ctrl+C` or `docker compose down`. PostgreSQL data is stored in a named Docker
volume and survives container stops; do not use `docker compose down -v` unless
you intend to delete that data.

The Expo container serves the web version of the React Native app. It does not
run iOS or Android simulators. For native device/simulator development, use the
Expo development server locally from `frontend/`.