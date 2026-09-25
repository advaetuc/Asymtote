"""ASGI entrypoint shared by Vercel and standalone Uvicorn."""

from api_app import create_app

app = create_app()
