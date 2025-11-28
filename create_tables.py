import asyncio
from app.config.database import engine, Base

# --- CRITICAL: Import your models here so Base knows about them ---
from app.models.user import User
# If your Device/Alert models are in app/models/device.py or similar, import them too:
# from app.models.device import Device 
# from app.models.alert import Alert
# -----------------------------------------------------------------

async def create_tables():
    print("⏳ Connecting to Supabase...")
    async with engine.begin() as conn:
        # This will create all tables based on your models
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Tables created successfully")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())