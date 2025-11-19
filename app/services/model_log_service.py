"""
Service for storing model logs and generating dashboard summaries.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func
from app.models.model_log import ModelLog
from app.db.session import AsyncSessionLocal

class ModelLogService:
    @staticmethod
    async def store_log(
        model_name: str,
        log_level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> ModelLog:
        """Store a new model log entry in the database."""
        log = ModelLog(
            model_name=model_name,
            log_level=log_level,
            message=message,
            extra=extra,
            timestamp=timestamp or datetime.utcnow()
        )
        async with AsyncSessionLocal() as session:
            session.add(log)
            await session.commit()
            await session.refresh(log)
        return log

    @staticmethod
    async def get_recent_logs(limit: int = 20) -> List[ModelLog]:
        """Get the most recent model logs."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ModelLog).order_by(ModelLog.timestamp.desc()).limit(limit)
            )
            return list(result.scalars())

    @staticmethod
    async def get_log_summary(since_hours: int = 24) -> Dict[str, Any]:
        """Get a summary of logs for the dashboard (counts, error rates, etc)."""
        since = datetime.utcnow() - timedelta(hours=since_hours)
        async with AsyncSessionLocal() as session:
            # Total logs
            total_logs = await session.scalar(
                select(func.count(ModelLog.id)).where(ModelLog.timestamp >= since)
            )
            # Error logs
            error_logs = await session.scalar(
                select(func.count(ModelLog.id)).where(
                    ModelLog.timestamp >= since,
                    ModelLog.log_level == "ERROR"
                )
            )
            # By model
            by_model = await session.execute(
                select(
                    ModelLog.model_name,
                    func.count(ModelLog.id)
                ).where(ModelLog.timestamp >= since).group_by(ModelLog.model_name)
            )
            model_counts = {row[0]: row[1] for row in by_model}
        return {
            "total_logs": total_logs,
            "error_logs": error_logs,
            "model_counts": model_counts,
        }
