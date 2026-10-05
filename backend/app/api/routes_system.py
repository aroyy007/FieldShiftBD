import logging

from fastapi import APIRouter
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine

router = APIRouter(tags=["System"])
logger = logging.getLogger(__name__)

@router.get("/")
def read_root():
    return {"message": "Welcome to the FieldShift Backend!"}

@router.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.exception("Database health check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from exc

    return {
        "status": "ok",
        "service": "FieldShift API",
        "version": "1.0.0",
        "database": "connected",
    }
