import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, Device
from app.schemas.alerts import AlertCreate
from app.schemas.devices import DeviceCreate


ALERT_TYPES = (
    "weapon_detection",
    "unauthorized_passenger",
    "aggression_detection",
)


class TestUtils:
    @staticmethod
    def create_test_device_data(device_id: str = "test-device") -> Dict[str, Any]:
        return {
            "device_id": device_id,
            "vehicle_make": "Toyota",
            "vehicle_model": "Camry",
        }
    
    @staticmethod
    def create_test_alert_data(
        device_id: str = "test-device",
        alert_type: str = "weapon_detection"
    ) -> Dict[str, Any]:
        return {
            "device_id": device_id,
            "alert_type": alert_type,
            "timestamp": datetime.utcnow().isoformat(),
            "location_lat": 6.5244,
            "location_lon": 3.3792,
            "payload": {
                "confidence": 0.95,
                "weapon_type": "handgun" if alert_type == "weapon_detection" else "",
            },
        }
    
    @staticmethod
    async def create_test_device(
        session: AsyncSession,
        device_data: Dict[str, Any] = None
    ) -> Device:
        if device_data is None:
            device_data = TestUtils.create_test_device_data()

        payload = DeviceCreate(**device_data).model_dump()
        device = Device(**payload)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        return device
    
    @staticmethod
    async def create_test_alert(
        session: AsyncSession,
        alert_data: Dict[str, Any] = None
    ) -> Alert:
        if alert_data is None:
            alert_data = TestUtils.create_test_alert_data()

        payload = AlertCreate(**alert_data).model_dump()
        alert = Alert(**payload, id=str(uuid.uuid4()))
        session.add(alert)
        await session.commit()
        await session.refresh(alert)
        return alert
    
    @staticmethod
    async def create_sample_data(
        session: AsyncSession,
        num_devices: int = 3,
        alerts_per_device: int = 10
    ) -> Dict[str, List[Any]]:
        devices = []
        alerts = []
        alert_types = ALERT_TYPES

        # Create devices
        for i in range(num_devices):
            device_id = f"test-device-{i}"
            device = await TestUtils.create_test_device(
                session,
                TestUtils.create_test_device_data(device_id)
            )
            devices.append(device)
            
            # Create alerts for each device
            for j in range(alerts_per_device):
                alert_type = alert_types[j % len(alert_types)]
                alert_data = TestUtils.create_test_alert_data(device_id, alert_type)
                alert_data["timestamp"] = (
                    datetime.utcnow() - timedelta(hours=j)
                ).isoformat()
                
                alert = await TestUtils.create_test_alert(session, alert_data)
                alerts.append(alert)
        
        return {
            "devices": devices,
            "alerts": alerts
        }
    
    @staticmethod
    def assert_alert_response(data: Dict[str, Any], expected_alert: Alert) -> None:
        assert data["device_id"] == expected_alert.device_id
        assert data["alert_type"] == expected_alert.alert_type
        assert datetime.fromisoformat(data["timestamp"]) == expected_alert.timestamp
        assert data.get("location_lat") == expected_alert.location_lat
        assert data.get("location_lon") == expected_alert.location_lon

        payload = expected_alert.payload
        if isinstance(payload, str):
            payload = json.loads(payload)
        assert data.get("payload", {}) == (payload or {})
    
    @staticmethod
    def assert_device_response(data: Dict[str, Any], expected_device: Device) -> None:
        assert data["device_id"] == expected_device.device_id
        assert data.get("vehicle_make") == expected_device.vehicle_make
        assert data.get("vehicle_model") == expected_device.vehicle_model


class BaseTestCase:
    @pytest_asyncio.fixture(autouse=True)
    async def setup_test_data(self, db_session: AsyncSession):
        self.session = db_session
        self.utils = TestUtils
        self.test_data = await self.utils.create_sample_data(db_session)
        self.devices = self.test_data["devices"]
        self.alerts = self.test_data["alerts"]
        
        yield
        
        for alert in self.alerts:
            await db_session.delete(alert)
        for device in self.devices:
            await db_session.delete(device)
        await db_session.commit()
    
    def assert_pagination(self, data: Dict[str, Any], expected_total: int) -> None:
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert data["total"] == expected_total
        assert len(data["items"]) <= data["size"]
    
    async def get_alerts_count(self) -> int:
        result = await self.session.execute(select(func.count(Alert.id)))
        return result.scalar_one()
    
    async def get_devices_count(self) -> int:
        result = await self.session.execute(select(func.count(Device.id)))
        return result.scalar_one()
    
    def create_json_file(self, data: Dict[str, Any], filename: str) -> str:
        import tempfile
        import os
        
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        with open(file_path, "w") as f:
            json.dump(data, f)
        
        return file_path