"""
Pydantic schemas for model log ingestion and summary responses.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel

class ModelLogCreate(BaseModel):
    model_name: str
    log_level: str
    message: str
    extra: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

class ModelLogOut(BaseModel):
    id: int
    timestamp: datetime
    model_name: str
    log_level: str
    message: str
    extra: Optional[Dict[str, Any]] = None

class ModelLogSummary(BaseModel):
    total_logs: int
    error_logs: int
    model_counts: Dict[str, int]
