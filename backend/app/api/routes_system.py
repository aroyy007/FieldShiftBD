from fastapi import APIRouter

router = APIRouter(tags=["System"])

@router.get("/")
def read_root():
    return {"message": "Welcome to the FieldShift Backend!"}

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "FieldShift API", "version": "1.0.0"}
