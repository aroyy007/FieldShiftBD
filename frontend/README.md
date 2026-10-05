# FieldShift Frontend

The frontend is an Expo / React Native application.

## Run the web app with Docker

From the repository root, create the local environment file and start the full stack:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The Expo web app is served at http://localhost:8082. After the first build,
`docker compose up` starts the services without rebuilding. Source changes are
mounted into the container for development.

Docker runs the web app only; it does not provide Android or iOS simulators.
For native development, use Expo locally:

```powershell
cd frontend
npm ci
npm start
```

Then use the Expo CLI options for a development build, Android emulator, iOS
simulator, or Expo Go. This project uses Expo Router; application routes live
under `src/app/`.
