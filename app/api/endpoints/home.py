"""Home endpoint handlers."""

import os
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(
    tags=["Interface"]
)


@router.get("/", summary="Home Page")
async def serve_homepage():
    """
    Serve the main HTML interface.
    
    Returns:
    - HTML page for interacting with WebSocket if index.html exists
    - Status message if index.html is not found
    """
    if not os.path.exists("index.html"):
        return {"status": "API is running. 'index.html' test page not found."}
    return FileResponse("index.html")


@router.get("/home", summary="Home Page (Alternative)")
async def serve_home():
    """Alternative endpoint for the main HTML interface."""
    return await serve_homepage()


@router.get("/index.html", summary="Home Page (Direct)")
async def serve_index():
    """Direct access to the HTML interface."""
    return await serve_homepage()