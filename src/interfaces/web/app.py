"""FastAPI application for health checks and OAuth callbacks."""

from fastapi import FastAPI

from src.interfaces.web.routes.gmail_oauth import router as gmail_oauth_router
from src.storage.dependencies import build_storage_dependencies

build_storage_dependencies()
app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(gmail_oauth_router)
