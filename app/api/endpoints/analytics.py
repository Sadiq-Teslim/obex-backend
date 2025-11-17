"""Alert analytics endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

import app.services.cache as cache_module
from app.services.alert_query import AlertQueryService

router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"]
)


@router.get(
    "/alerts/timeframe",
    summary="Get alerts within a timeframe",
    description="Retrieve alerts between specified start and end times."
)
async def get_alerts_by_timeframe(
    start_time: datetime = Query(..., description="Start time (ISO format)"),
    end_time: datetime = Query(..., description="End time (ISO format)"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    device_id: Optional[str] = Query(None, description="Filter by device ID")
):
    """Get alerts within a specific timeframe with optional filtering."""
    cache_key = cache_module.cache.get_key(
        "timeframe",
        start_time.isoformat(),
        end_time.isoformat(),
        str(alert_type),
        str(device_id)
    )
    
    return await cache_module.cache.get_or_set(
        cache_key,
        lambda: AlertQueryService.get_alerts_by_timeframe(
            start_time, end_time, alert_type, device_id
        )
    )


@router.get(
    "/alerts/location",
    summary="Get alerts near location",
    description="Retrieve alerts within a radius of specified coordinates."
)
async def get_alerts_by_location(
    lat: float = Query(..., description="Latitude", ge=-90.0, le=90.0),
    lon: float = Query(..., description="Longitude", ge=-180.0, le=180.0),
    radius_km: float = Query(1.0, description="Radius in kilometers", gt=0)
):
    """Get alerts within a radius of a location."""
    cache_key = cache_module.cache.get_key(
        "location",
        f"{lat:.4f}",
        f"{lon:.4f}",
        f"{radius_km:.1f}"
    )
    
    return await cache_module.cache.get_or_set(
        cache_key,
        lambda: AlertQueryService.get_alerts_by_location(lat, lon, radius_km)
    )


@router.get(
    "/alerts/counts",
    summary="Get alert counts by type",
    description="Get aggregated counts of alerts by type within optional timeframe."
)
async def get_alert_counts(
    start_time: Optional[datetime] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO format)")
):
    """Get aggregated counts of alerts by type."""
    cache_key = cache_module.cache.get_key(
        "counts",
        start_time.isoformat() if start_time else "all",
        end_time.isoformat() if end_time else "all"
    )
    
    return await cache_module.cache.get_or_set(
        cache_key,
        lambda: AlertQueryService.get_alert_counts_by_type(start_time, end_time)
    )


@router.get(
    "/alerts/trends",
    summary="Get alert trends",
    description="Get alert trends over time with specified interval."
)
async def get_alert_trends(
    days: int = Query(7, description="Number of days to analyze"),
    interval_hours: int = Query(24, description="Interval in hours")
):
    """Get alert trends over time."""
    cache_key = cache_module.cache.get_key("trends", str(days), str(interval_hours))
    
    return await cache_module.cache.get_or_set(
        cache_key,
        lambda: AlertQueryService.get_alert_trends(days, interval_hours)
    )


@router.get(
    "/devices/{device_id}/statistics",
    summary="Get device statistics",
    description="Get comprehensive statistics for a specific device."
)
async def get_device_statistics(device_id: str):
    """Get comprehensive statistics for a specific device."""
    cache_key = cache_module.cache.get_key("device", device_id, "stats")
    
    return await cache_module.cache.get_or_set(
        cache_key,
        lambda: AlertQueryService.get_device_statistics(device_id),
        expire=300  # Short cache time for device stats
    )