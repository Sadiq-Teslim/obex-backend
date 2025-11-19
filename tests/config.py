from pydantic import Field

from app.core.settings import Settings


class TestSettings(Settings):
    database_url: str = Field(default="sqlite+aiosqlite:///./test.db", alias="DATABASE_URL")
    test_database_url: str = Field(default="sqlite+aiosqlite:///./test.db", alias="TEST_DATABASE_URL")
    redis_db: int = Field(default=15, alias="REDIS_DB")
    cache_prefix: str = Field(default="test", alias="CACHE_PREFIX")
 
    class Config(Settings.Config):
        env_file = None
        case_sensitive = True


def get_test_settings() -> TestSettings:
    return TestSettings()