from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, get_settings
from .rag_pipeline import build_pipeline
from .routers import mcq_generator, query


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    origins = settings.get_allowed_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
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
    
    @app.get("/test-gemini")
    async def test_gemini() -> dict[str, Any]:
        """Test endpoint to check Gemini API connection."""
        from .services.llm_service import GeminiService
        from .config import get_settings
        
        settings = get_settings()
        try:
            llm = GeminiService(
                api_key=settings.gemini_api_key,
                api_url=settings.resolved_gemini_url,
            )
            result = await llm.generate_text("Say hello in Vietnamese")
            return {
                "status": "success",
                "model": settings.gemini_model,
                "api_url": settings.resolved_gemini_url,
                "response": result[:100] if result else "No response",
            }
        except Exception as e:
            return {
                "status": "error",
                "model": settings.gemini_model,
                "api_url": settings.resolved_gemini_url,
                "error": str(e),
            }

    return app


app = create_app()
