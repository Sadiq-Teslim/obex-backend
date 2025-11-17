"""Application settings and configuration helpers."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Pydantic powered settings loaded from environment variables."""

    database_url: str = Field(
        default="sqlite+aiosqlite:///./obex.db",
        alias="DATABASE_URL",
        description="Primary application database URL",
    )
    test_database_url: str = Field(
        default="sqlite+aiosqlite:///./test.db",
        alias="TEST_DATABASE_URL",
        description="Test database URL",
    )

    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: Optional[str] = Field(
        default=None,
        alias="REDIS_PASSWORD",
    )
    cache_prefix: str = Field(default="obex", alias="CACHE_PREFIX")
    cache_ttl: int = Field(default=3600, alias="CACHE_TTL")

    mqtt_broker_host: str = Field(
        default="test.mosquitto.org",
        alias="MQTT_BROKER_HOST",
    )
    mqtt_broker_port: int = Field(default=1883, alias="MQTT_BROKER_PORT")
    mqtt_alerts_topic: str = Field(default="obex/alerts", alias="MQTT_ALERTS_TOPIC")
    mqtt_username: Optional[str] = Field(default=None, alias="MQTT_USERNAME")
    mqtt_password: Optional[str] = Field(default=None, alias="MQTT_PASSWORD")
    mqtt_use_tls: bool = Field(default=False, alias="MQTT_USE_TLS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()


MQTT_CONFIG = {
    "BROKER_HOST": settings.mqtt_broker_host,
    "BROKER_PORT": settings.mqtt_broker_port,
    "ALERTS_TOPIC": settings.mqtt_alerts_topic,
    "USERNAME": settings.mqtt_username or "",
    "PASSWORD": settings.mqtt_password or "",
    "USE_TLS": bool(settings.mqtt_use_tls),
}


REDIS_CONFIG = {
    "HOST": settings.redis_host,
    "PORT": settings.redis_port,
    "DB": settings.redis_db,
    "PASSWORD": settings.redis_password,
    "PREFIX": settings.cache_prefix,
    "DEFAULT_TIMEOUT": settings.cache_ttl,
}


API_CONFIG = {
    "TITLE": "OBEX EDGE Backend API",
    "DESCRIPTION": """
    ## OBEX Vehicle Security System API
    
    Real-time security alert processing with MQTT and WebSocket support.
    
    ### Features:
    * Real-time alert creation and retrieval
    * Device registration and management
    * WebSocket live streaming of alerts
    * MQTT broker integration for edge devices
    
    ### Test Points:
    1. **Device Registration**: Register a new device with `/api/devices/register`
    2. **Alert Creation**: Send alerts via `/api/alerts` or MQTT
    3. **WebSocket**: Connect to `/ws/alerts` for real-time updates
    4. **Alert Retrieval**: List alerts with GET `/api/alerts`
    
    ### Important Notes:
    * **IDs are auto-generated** - Do NOT include `id` field when creating devices or alerts
    * All timestamps use ISO 8601 format (e.g., "2025-11-04T00:00:00Z")
    * WebSocket endpoint: `ws://localhost:8000/ws/alerts`
    * MQTT topic: `obex/alerts`
    
    ### Alert Types:
    - weapon_detection
    - unauthorized_passenger
    - aggression_detection
    - harassment_detection
    - robbery_pattern
    - route_deviation
    - driver_fatigue
    - distress_detection
    """,
    "VERSION": "0.2.0",
    "CONTACT": {
        "name": "OBEX Team",
        "url": "https://github.com/Sadiq-Teslim/obex-backend",
    },
    "LICENSE": {
        "name": "MIT",
    },
}