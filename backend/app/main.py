from contextlib import asynccontextmanager
import secrets

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.community import router as community_router
from app.api.discovery import router as discovery_router
from app.api.health import router as health_router
from app.api.interactions import router as interactions_router
from app.api.market import router as market_router
from app.api.notifications import router as notifications_router
from app.api.posts import router as posts_router
from app.api.social_users import router as social_users_router
from app.api.uploads import router as uploads_router
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
import app.models.community  # noqa: F401
import app.models.notification  # noqa: F401
import app.models.operations  # noqa: F401
import app.models.points  # noqa: F401


def seed_admin() -> None:
    """Create an initial admin user from environment settings (dev convenience)."""
    if not settings.database_url.startswith("sqlite"):
        return

    from app.core.security import get_password_hash
    from app.db.session import SessionLocal
    from app.models.user import AuthLevel, RegisterType, User, UserRole, UserStatus

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if existing:
            return
        admin = User(
            phone=settings.admin_phone,
            email=settings.admin_email,
            password_hash=get_password_hash(settings.admin_password),
            nickname=settings.admin_nickname,
            role=UserRole.ADMIN,
            auth_level=AuthLevel.VERIFIED,
            status=UserStatus.ACTIVE,
            register_type=RegisterType.EMAIL if "@" in settings.admin_email else RegisterType.PHONE,
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()


def seed_categories() -> None:
    from app.db.session import SessionLocal
    from app.models.content import Category

    # 以下旧分类保留在数据库但标记为不活跃（已从侧边栏移除，仅兼容旧数据）
    defaults = [
        ("综合讨论", "投资话题综合交流", 1, False),
        ("股票市场", "A股、港股与海外市场", 2, False),
        ("基金投资", "公募基金、ETF与定投", 3, True),   # 仍用于主题专区
        ("问答求助", "投资问题互助", 4, False),
        ("投资策略", "资产配置与策略研究", 5, False),
    ]
    # 公司研究专区行业分类
    industry_categories = [
        ("科技公司", "半导体、AI、互联网等科技公司深度讨论", 6),
        ("金融公司", "银行、券商、保险等金融公司研究", 7),
        ("医药公司", "医药生物、医疗器械、创新药等", 8),
        ("消费公司", "食品饮料、家电、零售等消费行业", 9),
        ("新能源", "光伏、锂电、风电、储能等新能源行业", 10),
        ("制造业", "高端装备、汽车、化工等制造业", 11),
    ]
    # 市场讨论区子板块
    market_categories = [
        ("A股", "A股市场讨论", 12),
        ("港股", "港股市场讨论", 13),
        ("美股", "美股市场讨论", 14),
        ("期货", "期货市场讨论", 15),
    ]
    # 主题专区子板块
    theme_categories = [
        ("价值投资", "价值投资理念与实践", 16),
        ("量化投资", "量化策略与程序化交易", 17),
        ("基金研究", "公募、私募、ETF等基金深度研究", 18),
        ("新股/新债", "新股申购与新债分析", 19),
        ("宏观策略", "宏观经济与市场策略", 20),
    ]
    # 问答求助区子板块
    qa_categories = [
        ("新手提问", "投资入门与基础问题", 21),
        ("投资解惑", "投资疑难问题解答", 22),
    ]
    db = SessionLocal()
    try:
        if db.query(Category).count() == 0:
            db.add_all(
                [Category(name=name, description=description, sort_order=order, is_active=active) for name, description, order, active in defaults]
            )
            db.add_all(
                [Category(name=name, description=description, sort_order=order) for name, description, order in industry_categories]
            )
            db.add_all(
                [Category(name=name, description=description, sort_order=order) for name, description, order in market_categories]
            )
            db.add_all(
                [Category(name=name, description=description, sort_order=order) for name, description, order in theme_categories]
            )
            db.add_all(
                [Category(name=name, description=description, sort_order=order) for name, description, order in qa_categories]
            )
            db.commit()
    finally:
        db.close()


def seed_demo_content() -> None:
    """Restore the original demo posts as real SQLite rows for local development."""
    if not settings.database_url.startswith("sqlite"):
        return

    from app.core.security import get_password_hash
    from app.db.session import SessionLocal
    from app.models.content import Category, Post
    from app.models.user import AuthLevel, RegisterType, User, UserStatus

    db = SessionLocal()
    try:
        if db.query(Post).count() > 0:
            return
        system_user = db.query(User).filter(User.phone == "00000000000").first()
        if system_user is None:
            system_user = User(
                phone="00000000000",
                password_hash=get_password_hash(secrets.token_urlsafe(32)),
                nickname="论坛演示账号",
                register_type=RegisterType.PHONE,
                auth_level=AuthLevel.BASIC,
                status=UserStatus.ACTIVE,
            )
            db.add(system_user)
            db.flush()

        categories = {item.name: item for item in db.query(Category).all()}
        demo_posts = [
            ("综合讨论", "A股市场今日讨论", "今天大盘震荡上行，成交量有所放大，新能源和半导体板块表现活跃。", ["A股", "大盘分析"]),
            ("基金投资", "指数基金长期配置思路", "宽基指数基金仍是长期配置的常用选择，可关注沪深300和中证500的定投机会。", ["指数基金", "定投", "配置"]),
            ("问答求助", "新手该怎么选基金？", "刚开始理财，想了解适合新手的基金筛选方法，欢迎大家交流。", ["新手", "基金入门"]),
            ("投资策略", "2026下半年投资策略展望", "结合宏观数据和市场估值，重点关注消费复苏和科技创新两条主线。", ["投资策略", "展望", "A股"]),
            ("股票市场", "港股通标的分析：腾讯VS阿里", "对比腾讯和阿里的估值、业务增长点和长期投资价值。", ["港股", "腾讯", "阿里"]),
        ]
        for index, (category_name, title, content, tags) in enumerate(demo_posts):
            category = categories[category_name]
            db.add(
                Post(
                    user_id=system_user.id,
                    category_id=category.id,
                    title=title,
                    content=content,
                    tags=tags,
                    like_count=(index + 1) * 4,
                    comment_count=index * 2,
                    view_count=(index + 1) * 120,
                    is_elite=index in (1, 3),
                )
            )
            category.post_count += 1
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all tables on startup (dev convenience — use migrations in production)."""
    Base.metadata.create_all(bind=engine)
    seed_admin()
    seed_categories()
    seed_demo_content()
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
    app.include_router(notifications_router, prefix="/api")
    app.include_router(community_router, prefix="/api")
    app.include_router(discovery_router, prefix="/api")
    app.include_router(admin_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(uploads_router, prefix="/api")

    # 静态文件服务（上传的附件）
    uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

    return app


app = create_app()
