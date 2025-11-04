# OBEX EDGE Backend API

FastAPI-based backend for the OBEX Vehicle Security System with real-time alert processing, MQTT integration, and WebSocket support.

## Features

- **Real-time Alerts**: MQTT subscriber receives and processes security alerts from edge devices
- **WebSocket Broadcasting**: Live alert streaming to connected web clients
- **Async Database**: SQLAlchemy async ORM with SQLite (local dev) or PostgreSQL (production)
- **RESTful API**: Device registration, alert management, and status endpoints
- **Type Safety**: Pydantic v2 schemas with validation

## Project Structure

```
obex_backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, routes, WebSocket, MQTT logic
│   ├── models.py            # SQLAlchemy database models
│   ├── schema.py            # Pydantic schemas for validation
│   └── config/
│       ├── __init__.py
│       └── database.py      # Database configuration
├── alembic/                 # Database migrations
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create this)
└── README.md
```

## Quick Start

### 1. Prerequisites

- Python 3.10+
- pip or conda

### 2. Install Dependencies

```cmd
pip install -r requirements.txt
```

### 3. Environment Setup

Create a `.env` file in the project root:

```env
# Database (defaults to SQLite if not set)
DATABASE_URL=sqlite+aiosqlite:///./test.db
# For PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/obex_db

# MQTT Broker Configuration
MQTT_BROKER_HOST=test.mosquitto.org
MQTT_BROKER_PORT=1883
MQTT_ALERTS_TOPIC=obex/alerts
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_USE_TLS=false
```

### 4. Run the Server

```cmd
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws/alerts

## API Endpoints

### Status & Health

- **GET** `/api/status` - Server status and active WebSocket connections

### Device Management

- **POST** `/api/devices/register` - Register a new edge device
  ```json
  {
    "device_id": "raspberry-pi-001",
    "vehicle_make": "Toyota",
    "vehicle_model": "Camry"
  }
  ```

### Alert Management

- **POST** `/api/alerts` - Create a new alert (also saves to DB and broadcasts via WebSocket)
  ```json
  {
    "device_id": "raspberry-pi-001",
    "timestamp": "2025-11-03T12:00:00Z",
    "alert_type": "weapon_detection",
    "location_lat": 6.5244,
    "location_lon": 3.3792,
    "payload": {"confidence": 0.95}
  }
  ```

- **GET** `/api/alerts` - Retrieve all alerts (ordered by timestamp desc)

### WebSocket

- **WS** `/ws/alerts` - Real-time alert streaming
  - Automatically broadcasts new alerts to all connected clients
  - Send any text to keep connection alive (receives pong response)

## Alert Types

The system supports the following alert types:
- `weapon_detection`
- `unauthorized_passenger`
- `aggression_detection`
- `harassment_detection`
- `robbery_pattern`
- `route_deviation`
- `driver_fatigue`
- `distress_detection`

## MQTT Integration

The backend subscribes to the configured MQTT topic and:
1. Validates incoming JSON messages against the `AlertCreate` schema
2. Saves valid alerts to the database
3. Broadcasts them to all connected WebSocket clients

### Publishing Test Alerts via MQTT

You can use `mosquitto_pub` or any MQTT client:

```bash
mosquitto_pub -h test.mosquitto.org -t obex/alerts -m '{
  "device_id": "test-device",
  "timestamp": "2025-11-03T12:00:00Z",
  "alert_type": "weapon_detection",
  "location_lat": 6.5244,
  "location_lon": 3.3792
}'
```

## Development

### Database Migrations (Alembic)

Generate a new migration:
```cmd
alembic revision --autogenerate -m "description"
```

Apply migrations:
```cmd
alembic upgrade head
```

### Running Tests

```cmd
pytest
```

### Code Style

```cmd
black app/
flake8 app/
```

## Production Deployment

### Environment Variables

For production, update `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@prod-host:5432/obex_prod
MQTT_BROKER_HOST=your-mqtt-broker.com
MQTT_BROKER_PORT=8883
MQTT_USERNAME=your_username
MQTT_PASSWORD=your_password
MQTT_USE_TLS=true
```

### Docker Deployment

Build and run with Docker Compose:

```cmd
docker-compose up -d
```

### Model Type Considerations

For **PostgreSQL production**, consider reverting to native PostgreSQL types in `app/models.py`:

```python
from sqlalchemy.dialects.postgresql import UUID, JSONB

# Change:
id = Column(String(36), ...)  # Current (portable)
# To:
id = Column(UUID(as_uuid=True), ...)  # PostgreSQL native

# Change:
payload = Column(JSON)  # Current (portable)
# To:
payload = Column(JSONB)  # PostgreSQL native (faster indexing)
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'aiosqlite'`:
```cmd
pip install aiosqlite python-dotenv
```

### Circular Import Errors

Ensure `app/config/database.py` does **not** import from `app.models` or `app.schema`.

### MQTT Connection Issues

- Verify broker host/port in `.env`
- Check firewall rules
- For TLS brokers, set `MQTT_USE_TLS=true`

### Pydantic Warnings

If you see `orm_mode` deprecation warnings, ensure all schemas use:
```python
model_config = {"from_attributes": True}
```

## License

MIT

## Contact

For issues or questions, please open an issue on the repository.
