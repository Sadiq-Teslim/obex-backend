"""Main application factory and initialization."""

import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import API_CONFIG
from app.config.database import connect_db, close_db
from app.services.mqtt_client import mqtt_service

from app.api.endpoints import alerts, analytics, devices, websocket, home, cameras, otp

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    """
    print("--- App Startup ---")
    await connect_db()
    
    print("Starting MQTT client thread...")
    mqtt_thread = threading.Thread(target=mqtt_service.start, daemon=True)
    mqtt_thread.start()
    
    yield
    
    print("--- App Shutdown ---")
    mqtt_service.stop()
    
    await close_db()
    print("--- Shutdown complete ---")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=API_CONFIG["TITLE"],
        description=API_CONFIG["DESCRIPTION"],
        version=API_CONFIG["VERSION"],
        lifespan=lifespan,
        contact=API_CONFIG["CONTACT"],
        license_info=API_CONFIG["LICENSE"]
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all for development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(home.router)
    
    from app.api.endpoints import auth
    app.include_router(auth.router)

    app.include_router(cameras.router)

    app.include_router(alerts.router)
    app.include_router(devices.router)
    app.include_router(analytics.router)
    app.include_router(websocket.router)
    
    app.include_router(otp.router)
    
    from app.api.endpoints import model_logs
    app.include_router(model_logs.router)

    return app

app = create_app()