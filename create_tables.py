import asyncio
from app.config.database import engine, Base
from app.models.user import User 
from app.models.camera import Camera # <--- Add this import

async def reset_tables():
    print("⏳ Resetting Database Tables (Drop & Create)...")
    async with engine.begin() as conn:
        # Drop everything to handle the schema change cleanly
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables reset successfully")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_tables())