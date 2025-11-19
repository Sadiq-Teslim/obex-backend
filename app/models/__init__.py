"""Initialize database models."""

from app.models.alert import Alert
from app.models.device import Device
from app.models.model_log import ModelLog

__all__ = ["Alert", "Device"]
__all__.append("ModelLog")