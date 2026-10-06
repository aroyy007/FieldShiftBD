from fastapi import FastAPI
from app.api import routes_system
from app.api import routes_m4_weather

app = FastAPI(title="FieldShift API")

app.include_router(routes_system.router)
app.include_router(routes_m4_weather.router)

