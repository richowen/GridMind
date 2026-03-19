"""GridMind FastAPI application entry point.
Starts APScheduler on startup, mounts all routers, exposes WebSocket endpoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.scheduler import scheduler
from app.routers import optimization, immersion, overrides, history, system
from app.websocket.manager import manager

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("GridMind starting up")
    scheduler.start()
    yield
    logger.info("GridMind shutting down")
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="GridMind API",
    version="1.0.0",
    description="Solar battery intelligence system",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(optimization.router, prefix="/api/v1")
app.include_router(immersion.router, prefix="/api/v1")
app.include_router(overrides.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "scheduler_running": scheduler.running}


@app.websocket("/ws")
async def websocket_endpoint(websocket):
    await manager.handle(websocket)
