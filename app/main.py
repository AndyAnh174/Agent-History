from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, get_settings
from .rag_pipeline import build_pipeline
from .routers import mcq_generator, query


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def setup_pipeline() -> None:
        app.state.pipeline = build_pipeline(settings)

    @app.on_event("shutdown")
    async def teardown_pipeline() -> None:
        pipeline = getattr(app.state, "pipeline", None)
        if pipeline:
            await pipeline.shutdown()

    app.include_router(query.router, prefix=settings.api_prefix)
    app.include_router(mcq_generator.router, prefix=settings.api_prefix)

    @app.get("/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
