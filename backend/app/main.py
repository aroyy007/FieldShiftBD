from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_disease, routes_farm_state, routes_system
from app.core.config import settings

app = FastAPI(title="FieldShift API")

cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include all module routers here.
app.include_router(routes_system.router)
app.include_router(routes_farm_state.router)
app.include_router(routes_disease.router)
