from fastapi import FastAPI
from app.api import routes_system
from app.api import routes_m4_weather

app = FastAPI(title="FieldShift API")

# Include all module routers here
app.include_router(routes_system.router)
app.include_router(routes_m4_weather.router)  # M4: Weather Intelligence & Alerts

