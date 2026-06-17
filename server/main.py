"""
main.py — Application entry point.

╔══════════════════════════════════════════════════════════════╗
║  THIS FILE IS COMPLETE — you do not need to change anything. ║
╚══════════════════════════════════════════════════════════════╝

This file does three things only:
  1. Creates the FastAPI app
  2. Sets up logging
  3. Registers the router from routes.py

All actual route logic lives in routes.py.
This separation is the standard pattern in production FastAPI projects.

HOW TO RUN:
  uvicorn server.main:app --reload

  Then open: http://localhost:8000/docs
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .models import create_tables
from .routes import router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="Secure Messenger — Stage 2",
    description="Authenticated, encrypted REST API for private messaging",
    version="2.0.0",
    lifespan=lifespan,
)

_frontend = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=_frontend), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(_frontend / "index.html")


@app.get("/chat", include_in_schema=False)
def chat():
    return FileResponse(_frontend / "chat.html")


app.include_router(router)
