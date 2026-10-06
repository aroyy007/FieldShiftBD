from fastapi import FastAPI
from app.api import routes_farm_state, routes_m4_weather, routes_system

app = FastAPI(title="FieldShift API")

app.include_router(routes_system.router)
app.include_router(routes_m4_weather.router)
app.include_router(routes_farm_state.router)
