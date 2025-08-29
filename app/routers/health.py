from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["Health"])

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "1.0.0"
    }
