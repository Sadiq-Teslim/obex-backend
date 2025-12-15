import asyncio
from app.config.database import engine, Base

# --- IMPORT ALL MODELS HERE ---
from app.models.user import User
from app.models.camera import Camera
from app.models.otp import OTP  

async def update_tables():
    print("Updating Database Tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables updated successfully")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(update_tables())