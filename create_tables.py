import asyncio
from app.config.database import engine, Base

async def create_tables():
    async with engine.begin() as conn:
        # This will create all tables based on your models
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Tables created successfully")

if __name__ == "__main__":
    asyncio.run(create_tables())
