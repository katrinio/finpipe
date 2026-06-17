"""FastAPI application for health checks and OAuth callbacks."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.interfaces.web.routes.gmail_oauth import router as gmail_oauth_router
from src.storage.dependencies import build_storage_dependencies


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    build_storage_dependencies()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(gmail_oauth_router)
