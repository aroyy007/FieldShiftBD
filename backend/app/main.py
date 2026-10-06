from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_farm_state, routes_m2_advisor, routes_system

app = FastAPI(title="FieldShift API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8082", "http://127.0.0.1:8082"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include all module routers here
app.include_router(routes_system.router)
app.include_router(routes_farm_state.router)
app.include_router(routes_m2_advisor.router)

