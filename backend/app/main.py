from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.posts import router as posts_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

# Ensure all models are registered with SQLAlchemy's metadata before create_all
import app.models.user  # noqa: F401
import app.models.refresh_token  # noqa: F401
import app.models.certification  # noqa: F401
import app.models.risk_assessment  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all tables on startup (dev convenience — use migrations in production)."""
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
        description="Stock and fund investment forum API.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api")
    app.include_router(posts_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")

    return app


app = create_app()
