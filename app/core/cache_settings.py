"""Redis cache configuration settings."""

REDIS_CONFIG = {
    "HOST": "localhost",
    "PORT": 6379,
    "DB": 0,
    "PREFIX": "obex:",
    "DEFAULT_TIMEOUT": 3600  # 1 hour
}