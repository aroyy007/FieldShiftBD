from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.api import (
    routes_disease,
    routes_farm_state,
    routes_m1_profile,
    routes_m2_advisor,
    routes_m4_weather,
    routes_system,
)

from app.core.config import settings
from app.core.security import decode_access_token

app = FastAPI(title="FieldShift API")


# ── Auth middleware ────────────────────────────────────────────────────────────
# Runs on every single request before any route handler.
# Reads the Authorization header, decodes the JWT, and stamps the farmer's
# identity onto request.state so all route handlers can read it via
# get_current_farmer_id() from app.core.auth.
#
# If the token is missing or invalid, nothing is stamped — routes that require
# auth will raise 401 themselves via get_current_farmer_id().
# Public routes (register, login, health) don't call get_current_farmer_id()
# so they work fine without a token.

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # strip "Bearer " prefix
            farmer_id = decode_access_token(token)
            if farmer_id is not None:
                request.state.current_farmer_id = farmer_id
        return await call_next(request)


app.add_middleware(AuthMiddleware)


# ── CORS middleware ────────────────────────────────────────────────────────────
cors_origins = [
    origin.strip()
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ── Routers ────────────────────────────────────────────────────────────────────
# Include all module routers here.
app.include_router(routes_system.router)
app.include_router(routes_m1_profile.router)   # Module 1 — Profile & Onboarding
app.include_router(routes_m2_advisor.router)   # Module 2 — Crop Advisor
app.include_router(routes_m4_weather.router)   # Module 4 — Weather Intelligence
app.include_router(routes_farm_state.router)   # Module 3 — Farm Brain
app.include_router(routes_disease.router)      # Module 6 — Disease Detection
