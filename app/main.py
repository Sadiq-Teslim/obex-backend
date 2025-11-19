"""Main application factory and initialization."""

import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import API_CONFIG
from app.config.database import connect_db, close_db
from app.services.mqtt_client import mqtt_service

from app.api.endpoints import alerts, analytics, devices, websocket, home


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    """
    # --- STARTUP ---
    print("--- App Startup ---")
    # 1. Connect to DB and create tables
    await connect_db()
    
    # 2. Start the MQTT client loop in a daemon thread
    print("Starting MQTT client thread...")
    mqtt_thread = threading.Thread(target=mqtt_service.start, daemon=True)
    mqtt_thread.start()
    
    yield # The application is now running
    
    # --- SHUTDOWN ---
    print("--- App Shutdown ---")
    # 1. Disconnect MQTT client
    mqtt_service.stop()
    
    # 2. Close DB connection
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

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all for development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(home.router)
    app.include_router(alerts.router)
    app.include_router(devices.router)
    app.include_router(analytics.router)
    app.include_router(websocket.router)
    from app.api.endpoints import model_logs
    app.include_router(model_logs.router)

    return app


# Create the application instance
app = create_app()
