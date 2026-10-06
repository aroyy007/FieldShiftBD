from fastapi import FastAPI
from app.api import routes_farm_state, routes_system

app = FastAPI(title="FieldShift API")

# Include all module routers here
app.include_router(routes_system.router)
app.include_router(routes_farm_state.router)

