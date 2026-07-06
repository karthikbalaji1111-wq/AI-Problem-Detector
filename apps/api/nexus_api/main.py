from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nexus_api.config import get_settings
from nexus_api.database import SessionLocal, create_db_and_tables
from nexus_api.rate_limit import RateLimitMiddleware
from nexus_api.routers import agents, analytics, approvals, auth, connectors, organizations, tasks
from nexus_api.seed import seed_demo
from nexus_api.telemetry import configure_logging, configure_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    create_db_and_tables()
    if settings.seed_demo:
        with SessionLocal() as db:
            seed_demo(db)
    yield


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(
        title="NEXUS API",
        version="0.1.0",
        description="The Autonomous AI Workforce backend.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)
    app.include_router(auth.router, prefix="/v1")
    app.include_router(organizations.router, prefix="/v1")
    app.include_router(agents.router, prefix="/v1")
    app.include_router(tasks.router, prefix="/v1")
    app.include_router(approvals.router, prefix="/v1")
    app.include_router(connectors.router, prefix="/v1")
    app.include_router(analytics.router, prefix="/v1")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "nexus-api"}

    configure_telemetry(app)
    return app


app = create_app()
