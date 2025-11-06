"""Enhanced alert queries and utilities."""

from datetime import datetime, timedelta
import math
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.sql import and_

from app.models import Alert
from app.db.session import AsyncSessionLocal


class AlertQueryService:
    """Service for complex alert queries and aggregations."""

    @staticmethod
    async def get_alerts_by_timeframe(
        start_time: datetime,
        end_time: datetime,
        alert_type: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> List[Alert]:
        """Get alerts within a specific timeframe with optional filtering."""
        if end_time < start_time:
            raise ValueError("end_time must be greater than or equal to start_time")

        async with AsyncSessionLocal() as session:
            query = select(Alert).where(
                and_(Alert.timestamp >= start_time, Alert.timestamp <= end_time)
            )
            
            if alert_type:
                query = query.where(Alert.alert_type == alert_type)
            if device_id:
                query = query.where(Alert.device_id == device_id)
                
            result = await session.execute(query)
            return list(result.scalars())

    @staticmethod
    async def get_alerts_by_location(
        lat: float,
        lon: float,
        radius_km: float = 1.0
    ) -> List[Alert]:
        """Get alerts within a radius of a location."""
        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
            raise ValueError("Invalid latitude or longitude supplied")
        if radius_km <= 0:
            raise ValueError("radius_km must be positive")

        async with AsyncSessionLocal() as session:
            lat_range = radius_km / 111.0  # Rough conversion: 1° latitude ≈ 111 km
            cos_lat = math.cos(math.radians(lat)) or 1e-6
            lon_range = radius_km / (111.0 * abs(cos_lat))

            query = select(Alert).where(
                and_(
                    Alert.location_lat.between(lat - lat_range, lat + lat_range),
                    Alert.location_lon.between(lon - lon_range, lon + lon_range),
                )
            )

            result = await session.execute(query)
            return list(result.scalars())

    @staticmethod
    async def get_alert_counts_by_type(
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Get aggregated counts of alerts by type."""
        async with AsyncSessionLocal() as session:
            query = select(
                Alert.alert_type,
                func.count(Alert.id).label('count')
            )
            
            if start_time and end_time:
                query = query.where(
                    and_(
                        Alert.timestamp >= start_time,
                        Alert.timestamp <= end_time
                    )
                )
                
            query = query.group_by(Alert.alert_type)
            result = await session.execute(query)
            return {r[0]: r[1] for r in result}

    @staticmethod
    async def get_alert_trends(
        days: int = 7,
        interval_hours: int = 24
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get alert trends over time."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        async with AsyncSessionLocal() as session:
            bucket_size = "hour" if interval_hours < 24 else "day"
            bind = session.get_bind()
            dialect_name = getattr(getattr(bind, "dialect", None), "name", "")
            is_sqlite = dialect_name == "sqlite"

            if is_sqlite:
                date_format = "%Y-%m-%d %H:00:00" if bucket_size == "hour" else "%Y-%m-%d"
                bucket_expression = func.strftime(date_format, Alert.timestamp).label("bucket")
            else:
                bucket_expression = func.date_trunc(bucket_size, Alert.timestamp).label("bucket")

            query = (
                select(
                    Alert.alert_type,
                    bucket_expression,
                    func.count(Alert.id).label("count"),
                )
                .where(
                    and_(Alert.timestamp >= start_time, Alert.timestamp <= end_time)
                )
                .group_by(Alert.alert_type, bucket_expression)
                .order_by(bucket_expression)
            )

            result = await session.execute(query)

            trends: Dict[str, List[Dict[str, Any]]] = {}
            for alert_type, bucket_value, count in result:
                bucket_str = (
                    bucket_value.isoformat()
                    if hasattr(bucket_value, "isoformat")
                    else str(bucket_value)
                )
                trends.setdefault(alert_type, []).append({"date": bucket_str, "count": count})

            return trends

    @staticmethod
    async def get_device_statistics(device_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a specific device."""
        async with AsyncSessionLocal() as session:
            # Get total alerts
            total_query = select(func.count(Alert.id)).where(Alert.device_id == device_id)
            total_result = await session.execute(total_query)
            total_alerts = total_result.scalar()
            
            # Get alerts by type
            type_query = select(
                Alert.alert_type,
                func.count(Alert.id).label('count')
            ).where(
                Alert.device_id == device_id
            ).group_by(Alert.alert_type)
            type_result = await session.execute(type_query)
            alerts_by_type = {r[0]: r[1] for r in type_result}
            
            # Get latest alert
            latest_query = select(Alert).where(
                Alert.device_id == device_id
            ).order_by(Alert.timestamp.desc()).limit(1)
            latest_result = await session.execute(latest_query)
            latest_alert = latest_result.scalar()
            
            return {
                'total_alerts': total_alerts,
                'alerts_by_type': alerts_by_type,
                'latest_alert': latest_alert,
                'last_seen': latest_alert.timestamp if latest_alert else None
            }