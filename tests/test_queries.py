"""Tests for the alert query service."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio

from app.models import Alert
from app.services.alert_query import AlertQueryService


@pytest_asyncio.fixture
async def seeded_alerts(db_session):
    """Insert a handful of alerts covering multiple devices and types."""

    base_time = datetime.utcnow()
    alert_types = [
        "weapon_detection",
        "unauthorized_passenger",
        "aggression_detection",
    ]

    alerts = []
    for index, alert_type in enumerate(alert_types):
        alert = Alert(
            id=str(uuid4()),
            device_id=f"device-{index}",
            timestamp=base_time - timedelta(minutes=index * 10),
            alert_type=alert_type,
            location_lat=6.5 + (index * 0.01),
            location_lon=3.3 + (index * 0.01),
            payload={"sample": index},
        )
        alerts.append(alert)
        db_session.add(alert)

    await db_session.commit()
    return alerts


@pytest.mark.asyncio
async def test_get_alerts_by_timeframe(seeded_alerts) -> None:
    """Alerts within the provided timeframe should be returned."""

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)

    alerts = await AlertQueryService.get_alerts_by_timeframe(start_time, end_time)
    assert alerts
    assert all(start_time <= alert.timestamp <= end_time for alert in alerts)


@pytest.mark.asyncio
async def test_get_alerts_by_timeframe_filters(seeded_alerts) -> None:
    """Alert type and device filters reduce the result set."""

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)

    filtered = await AlertQueryService.get_alerts_by_timeframe(
        start_time,
        end_time,
        alert_type="weapon_detection",
        device_id="device-0",
    )
    assert filtered
    assert {alert.alert_type for alert in filtered} == {"weapon_detection"}
    assert {alert.device_id for alert in filtered} == {"device-0"}


@pytest.mark.asyncio
async def test_get_alerts_by_timeframe_invalid_range() -> None:
    """An invalid timeframe should raise a helpful error."""

    end_time = datetime.utcnow()
    start_time = end_time + timedelta(minutes=1)

    with pytest.raises(ValueError):
        await AlertQueryService.get_alerts_by_timeframe(start_time, end_time)


@pytest.mark.asyncio
async def test_get_alerts_by_location(seeded_alerts) -> None:
    """Location search should honour the radius filter."""

    alerts = await AlertQueryService.get_alerts_by_location(6.5, 3.3, radius_km=5.0)
    assert len(alerts) == len(seeded_alerts)

    none_found = await AlertQueryService.get_alerts_by_location(0.0, 0.0, radius_km=1.0)
    assert none_found == []


@pytest.mark.asyncio
async def test_get_alerts_by_location_invalid_inputs() -> None:
    """Bad coordinates trigger validation errors."""

    with pytest.raises(ValueError):
        await AlertQueryService.get_alerts_by_location(95.0, 0.0, radius_km=1.0)

    with pytest.raises(ValueError):
        await AlertQueryService.get_alerts_by_location(6.0, 200.0, radius_km=1.0)

    with pytest.raises(ValueError):
        await AlertQueryService.get_alerts_by_location(6.0, 3.0, radius_km=0.0)


@pytest.mark.asyncio
async def test_get_alert_counts_by_type(seeded_alerts) -> None:
    """Counts by type should reflect inserted alerts."""

    counts = await AlertQueryService.get_alert_counts_by_type()
    assert counts
    assert sum(counts.values()) == len(seeded_alerts)


@pytest.mark.asyncio
async def test_get_alert_trends(seeded_alerts) -> None:
    """Trend data returns per-type buckets with counts."""

    trends = await AlertQueryService.get_alert_trends(days=1, interval_hours=6)
    assert isinstance(trends, dict)
    assert trends
    first_key = next(iter(trends))
    assert {"date", "count"}.issubset(trends[first_key][0].keys())


@pytest.mark.asyncio
async def test_get_device_statistics(seeded_alerts) -> None:
    """Device statistics include totals and last seen timestamp."""

    stats = await AlertQueryService.get_device_statistics("device-0")
    assert stats["total_alerts"] == 1
    assert stats["alerts_by_type"] == {"weapon_detection": 1}
    assert stats["last_seen"] is not None