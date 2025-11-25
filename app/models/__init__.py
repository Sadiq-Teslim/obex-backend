"""Initialize database models."""

from app.models.alert import Alert
from app.models.device import Device
from app.models.model_log import ModelLog
from app.models.user import User

__all__ = ["Alert", "Device", "User"]
__all__.append("ModelLog")