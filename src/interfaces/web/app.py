"""FastAPI application for health checks and OAuth callbacks."""

from fastapi import FastAPI

from src.interfaces.web.routes.gmail_oauth import router as gmail_oauth_router

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(gmail_oauth_router)
