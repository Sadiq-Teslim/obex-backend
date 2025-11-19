"""
API endpoints for model log ingestion and dashboard summary.
"""
from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.model_log import ModelLogCreate, ModelLogOut, ModelLogSummary
from app.services.model_log_service import ModelLogService

router = APIRouter(
    prefix="/api/model-logs",
    tags=["Model Logs"]
)

@router.post("/", response_model=ModelLogOut, status_code=201)
async def ingest_model_log(log: ModelLogCreate):
    """Ingest a new model log entry."""
    result = await ModelLogService.store_log(**log.dict())
    if result:
        return result
    raise HTTPException(status_code=500, detail="Failed to store model log.")

@router.get("/recent", response_model=List[ModelLogOut])
async def get_recent_model_logs(limit: int = 20):
    """Get recent model logs."""
    return await ModelLogService.get_recent_logs(limit=limit)

@router.get("/summary", response_model=ModelLogSummary)
async def get_model_log_summary(since_hours: int = 24):
    """Get dashboard summary of model logs."""
    return await ModelLogService.get_log_summary(since_hours=since_hours)
