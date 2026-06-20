from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.interactions import router as interactions_router
from app.api.market import router as market_router
from app.api.posts import router as posts_router
from app.api.social_users import router as social_users_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

# Ensure all models are registered with SQLAlchemy's metadata before create_all
import app.config  # noqa: F401
import app.models.user  # noqa: F401
import app.models.refresh_token  # noqa: F401
import app.models.certification  # noqa: F401
import app.models.risk_assessment  # noqa: F401
import app.models.content  # noqa: F401
import app.models.social  # noqa: F401


def seed_categories() -> None:
    from app.db.session import SessionLocal
    from app.models.content import Category

    defaults = [
        ("综合讨论", "投资话题综合交流", 1),
        ("股票市场", "A股、港股与海外市场", 2),
        ("基金投资", "公募基金、ETF与定投", 3),
        ("问答求助", "投资问题互助", 4),
        ("投资策略", "资产配置与策略研究", 5),
    ]
    db = SessionLocal()
    try:
        if db.query(Category).count() == 0:
            db.add_all(
                [Category(name=name, description=description, sort_order=order) for name, description, order in defaults]
            )
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all tables on startup (dev convenience — use migrations in production)."""
    Base.metadata.create_all(bind=engine)
    seed_categories()
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
        allow_origin_regex=settings.allowed_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api")
    app.include_router(market_router, prefix="/api")
    app.include_router(posts_router, prefix="/api")
    app.include_router(interactions_router, prefix="/api")
    app.include_router(social_users_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")

    return app


app = create_app()
