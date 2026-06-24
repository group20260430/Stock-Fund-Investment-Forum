from datetime import date, datetime, timedelta, timezone
import re

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, desc
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin, get_current_user
from app.db.session import get_db
from app.models.certification import Certification, CertificationStatus
from app.models.professional_certification import ProfessionalCertification, ProfessionalCertStatus
from app.models.content import Category, Comment, CommentStatus, Like, Post, PostStatus, Share
from app.models.notification import Notification, NotificationType
from app.models.operations import (
    ActivityType,
    BanAction,
    BanRecord,
    ComplianceCategory,
    ComplianceRule,
    Report,
    ReportReason,
    ReportStatus,
    ReportTarget,
    ReviewAction,
    ReviewLog,
    ReviewTarget,
    SensitiveLevel,
    SensitiveWord,
    UserActivityLog,
)
from app.models.user import AuthLevel, User, UserStatus
from app.schemas.operations import (
    BanRequest,
    CategoryRequest,
    CertificationReviewRequest,
    ComplianceCheckRequest,
    ComplianceRuleCreate,
    DuplicateScanRequest,
    ReportCreate,
    ReportHandleRequest,
    ReviewRequest,
    SensitiveWordRequest,
)
from app.schemas.user import ApiResponse
from app.services.compliance_service import check_compliance, check_compliance_single_text
from app.services.duplicate_content_service import check_duplicate_post_content
from app.services.sensitive_word_service import check_sensitive_texts

router = APIRouter(tags=["admin"])


def _create_admin_alert(db: Session, title: str, content: str, target_type: str | None = None, target_id: int | None = None) -> None:
    """向所有管理员推送系统告警通知。"""
    admins = db.query(User).filter(User.role == UserRole.ADMIN, User.status == UserStatus.ACTIVE).all()
    for admin in admins:
        db.add(Notification(
            user_id=admin.id,
            type=NotificationType.SYSTEM_ALERT,
            title=title,
            content=content[:500],
            target_type=target_type,
            target_id=target_id,
        ))


def _validate_report_target(db: Session, target_type: str, target_id: int) -> None:
    model = {"post": Post, "comment": Comment, "user": User}[target_type]
    if db.query(model).filter(model.id == target_id).first() is None:
        raise HTTPException(status_code=404, detail="举报目标不存在")


@router.post("/report", status_code=201)
def submit_report(
    data: ReportCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_report_target(db, data.target_type, data.target_id)
    existing = db.query(Report).filter(
        Report.reporter_id == user.id,
        Report.target_type == ReportTarget(data.target_type),
        Report.target_id == data.target_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="已举报过该内容")
    report = Report(
        reporter_id=user.id,
        target_type=ReportTarget(data.target_type),
        target_id=data.target_id,
        reason=ReportReason(data.reason),
        description=data.description,
    )
    db.add(report)
    db.commit()
    return ApiResponse(code=201, message="举报已提交", data={"id": report.id})


@router.get("/admin/review-queue")
def review_queue(
    status: str = Query("pending", pattern="^(pending|approved|rejected)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    post_status = {"pending": PostStatus.REVIEWING, "approved": PostStatus.PUBLISHED, "rejected": PostStatus.REJECTED}[status]
    comment_status = {"pending": CommentStatus.REVIEWING, "approved": CommentStatus.PUBLISHED, "rejected": CommentStatus.REJECTED}[status]
    posts = db.query(Post).filter(Post.status == post_status).all()
    comments = db.query(Comment).filter(Comment.status == comment_status).all()

    def _compute_flags(item, content_type, texts):
        """Run all content checks to determine why this item was flagged for review."""
        flags = []
        title, body = (texts[0], texts[1]) if len(texts) > 1 else (texts[0], None)
        candidates = [t for t in [title, body] if t]
        if not candidates:
            return flags
        try:
            sw = check_sensitive_texts(db, candidates)
            if sw.matched_words:
                for w in sw.matched_words[:3]:
                    flags.append(f"sensitive:{w}")
        except Exception:
            pass
        try:
            comp = check_compliance(db, candidates)
            for m in comp.matches[:3]:
                flags.append(f"compliance:{m.rule_name}")
        except Exception:
            pass
        if content_type == "post" and body:
            try:
                dup = check_duplicate_post_content(db, item.user_id, title, body)
                if dup.should_review and dup.similarity:
                    flags.append(f"duplicate:{int(dup.similarity * 100)}%")
                elif dup.should_block:
                    flags.append("duplicate:exact_match")
            except Exception:
                pass
        return flags

    items = [
        {
            "id": f"post-{item.id}",
            "content_type": "post",
            "title": item.title,
            "author": {"id": item.author.id, "nickname": item.author.nickname},
            "flags": _compute_flags(item, "post", [item.title, item.content]),
            "status": status,
            "submitted_at": item.created_at,
        }
        for item in posts
    ] + [
        {
            "id": f"comment-{item.id}",
            "content_type": "comment",
            "title": item.content[:80],
            "author": {"id": item.author.id, "nickname": item.author.nickname},
            "flags": _compute_flags(item, "comment", [item.content]),
            "status": status,
            "submitted_at": item.created_at,
        }
        for item in comments
    ]
    items.sort(key=lambda item: item["submitted_at"], reverse=True)
    total = len(items)
    return ApiResponse(code=200, message="success", data={
        "items": items[(page - 1) * size:page * size], "total": total, "page": page, "size": size
    })


@router.post("/admin/review-queue/{review_id}/review")
def perform_review(
    review_id: str,
    data: ReviewRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        target_type, raw_id = review_id.split("-", 1)
        target_id = int(raw_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="无效的审核项ID") from None
    if target_type == "post":
        target = db.query(Post).filter(Post.id == target_id).first()
        if target:
            target.status = PostStatus.PUBLISHED if data.action in ("approve", "edit") else PostStatus.REJECTED
    elif target_type == "comment":
        target = db.query(Comment).filter(Comment.id == target_id).first()
        if target:
            target.status = CommentStatus.PUBLISHED if data.action in ("approve", "edit") else CommentStatus.REJECTED
    else:
        target = None
    if target is None:
        raise HTTPException(status_code=404, detail="审核项不存在")
    db.add(ReviewLog(
        target_type=ReviewTarget(target_type),
        target_id=target_id,
        reviewer_id=admin.id,
        action=ReviewAction(data.action),
        comment=data.comment,
    ))
    db.commit()
    return ApiResponse(code=200, message="审核完成", data={"status": target.status.value})


@router.get("/admin/users")
def admin_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    status: str | None = Query(None, pattern="^(active|disabled)$"),
    keyword: str | None = Query(None, max_length=100),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if status:
        query = query.filter(User.status == UserStatus(status))
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(or_(User.nickname.ilike(pattern), User.phone.ilike(pattern)))
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size).all()
    items = [
        {
            "id": user.id,
            "nickname": user.nickname,
            "phone": user.phone[:3] + "****" + user.phone[-4:],
            "avatar_url": user.avatar_url,
            "role": user.role.value,
            "status": user.status.value,
            "auth_level": user.auth_level.value,
            "followers_count": user.followers_count,
            "created_at": user.created_at,
            "ban_expires_at": user.ban_expires_at,
            "banned_reason": user.banned_reason,
        }
        for user in users
    ]
    return ApiResponse(code=200, message="success", data={"items": items, "total": total, "page": page, "size": size})


@router.post("/admin/users/{user_id}/ban")
def ban_user(
    user_id: int,
    data: BanRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    target = db.query(User).filter(User.id == user_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="不能封禁自己")
    if data.action == "ban":
        target.status = UserStatus.DISABLED
        target.banned_reason = data.reason
        target.ban_expires_at = (
            datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=data.duration_hours)
            if data.duration_hours else None
        )
    else:
        target.status = UserStatus.ACTIVE
        target.banned_reason = None
        target.ban_expires_at = None
    db.add(BanRecord(
        user_id=target.id,
        admin_id=admin.id,
        action=BanAction(data.action),
        reason=data.reason,
        duration_hours=data.duration_hours,
    ))
    db.commit()
    return ApiResponse(code=200, message="操作成功", data={"status": target.status.value})


def _today_count(db: Session, model, column) -> int:
    return db.query(model).filter(func.date(column) == date.today().isoformat()).count()


@router.get("/admin/stats/overview")
def stats_overview(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    active_ids = set()
    for model, user_column, time_column in (
        (Post, Post.user_id, Post.created_at),
        (Comment, Comment.user_id, Comment.created_at),
        (Like, Like.user_id, Like.created_at),
    ):
        active_ids.update(
            row[0] for row in db.query(user_column).filter(func.date(time_column) == date.today().isoformat()).distinct().all()
        )
    # 近7天趋势数据
    dates, active_users, new_posts, new_comments = [], [], [], []
    for offset in range(6, -1, -1):
        current = date.today() - timedelta(days=offset)
        key = current.isoformat()
        active = set(
            row[0] for row in db.query(Post.user_id).filter(func.date(Post.created_at) == key).distinct().all()
        ) | set(
            row[0] for row in db.query(Comment.user_id).filter(func.date(Comment.created_at) == key).distinct().all()
        )
        dates.append(key)
        active_users.append(len(active))
        new_posts.append(db.query(Post).filter(func.date(Post.created_at) == key).count())
        new_comments.append(db.query(Comment).filter(func.date(Comment.created_at) == key).count())
    # 热门话题
    tag_counts: dict[str, int] = {}
    for tags, in db.query(Post.tags).all():
        for tag in tags or []:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    hot_topics = [
        {"name": tag, "count": count}
        for tag, count in sorted(tag_counts.items(), key=lambda item: item[1], reverse=True)[:10]
    ]
    # 系统告警统计
    alert_count = db.query(Notification).filter(
        Notification.type == NotificationType.SYSTEM_ALERT,
        Notification.is_read.is_(False),
    ).count()
    suspicious_today = db.query(Notification).filter(
        Notification.type == NotificationType.SYSTEM_ALERT,
        func.date(Notification.created_at) == date.today().isoformat(),
    ).count()

    return ApiResponse(code=200, message="success", data={
        "daily_active_users": len(active_ids),
        "new_users_today": _today_count(db, User, User.created_at),
        "total_posts": db.query(Post).count(),
        "total_comments": db.query(Comment).count(),
        "pending_review": db.query(Post).filter(Post.status == PostStatus.REVIEWING).count()
        + db.query(Comment).filter(Comment.status == CommentStatus.REVIEWING).count(),
        "reports_today": _today_count(db, Report, Report.created_at),
        "unread_alerts": alert_count,
        "suspicious_today": suspicious_today,
        "trend": {"dates": dates, "active_users": active_users, "new_posts": new_posts, "new_comments": new_comments},
        "hot_topics": hot_topics,
        "hot_stocks": [],
    })


@router.get("/admin/stats/trend")
def stats_trend(
    period: str = Query("weekly", pattern="^(daily|weekly|monthly)$"),
    start_date: date | None = None,
    end_date: date | None = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    end = end_date or date.today()
    if start_date:
        start = start_date
    else:
        start = end - timedelta(days={"daily": 0, "weekly": 6, "monthly": 29}[period])
    days = (end - start).days + 1
    if days < 1 or days > 366:
        raise HTTPException(status_code=400, detail="日期范围无效")
    user_activity = []
    content_stats = []
    for offset in range(days):
        current = start + timedelta(days=offset)
        key = current.isoformat()
        new_users = db.query(User).filter(func.date(User.created_at) == key).count()
        posts = db.query(Post).filter(func.date(Post.created_at) == key).count()
        comments = db.query(Comment).filter(func.date(Comment.created_at) == key).count()
        active = set(
            row[0] for row in db.query(Post.user_id).filter(func.date(Post.created_at) == key).distinct().all()
        ) | set(
            row[0] for row in db.query(Comment.user_id).filter(func.date(Comment.created_at) == key).distinct().all()
        )
        user_activity.append({"date": key, "dau": len(active), "new_users": new_users})
        content_stats.append({"date": key, "posts": posts, "comments": comments})
    tag_counts: dict[str, int] = {}
    for tags, in db.query(Post.tags).all():
        for tag in tags or []:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    hot_topics = [
        {"topic": tag, "discussions": count, "trend": "stable"}
        for tag, count in sorted(tag_counts.items(), key=lambda item: item[1], reverse=True)[:10]
    ]
    return ApiResponse(code=200, message="success", data={
        "user_activity": user_activity, "content_stats": content_stats, "hot_topics": hot_topics
    })


@router.get("/admin/stats/hot-topics")
def hot_topics_analysis(
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    top_n: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """热门话题深度分析：按标签聚合，计算综合热度值，对比上期趋势"""
    days_map = {"daily": 1, "weekly": 7, "monthly": 30}
    days = days_map[period]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now - timedelta(days=days)
    prev_cutoff = cutoff - timedelta(days=days)

    def _aggregate_tags(since: datetime, until: datetime) -> dict[str, dict]:
        """聚合时间段内的标签统计数据"""
        posts = (
            db.query(Post)
            .filter(
                Post.status == PostStatus.PUBLISHED,
                Post.created_at >= since,
                Post.created_at <= until,
            )
            .all()
        )
        tags: dict[str, dict] = {}
        for post in posts:
            tag_list = post.tags or ([post.category.name] if post.category else [])
            for tag in tag_list:
                entry = tags.setdefault(tag, {
                    "post_count": 0,
                    "total_views": 0,
                    "total_likes": 0,
                    "total_comments": 0,
                    "total_collects": 0,
                    "heat_score": 0,
                })
                entry["post_count"] += 1
                entry["total_views"] += post.view_count or 0
                entry["total_likes"] += post.like_count or 0
                entry["total_comments"] += post.comment_count or 0
                entry["total_collects"] += post.collect_count or 0
        for tag_data in tags.values():
            tag_data["heat_score"] = (
                tag_data["total_views"]
                + tag_data["total_likes"] * 5
                + tag_data["total_comments"] * 8
                + tag_data["total_collects"] * 4
            )
        return tags

    current_tags = _aggregate_tags(cutoff, now)
    previous_tags = _aggregate_tags(prev_cutoff, cutoff)

    # Build ranked items with trend
    ranked = sorted(current_tags.items(), key=lambda kv: kv[1]["heat_score"], reverse=True)
    items = []
    for rank, (tag_name, data) in enumerate(ranked[:top_n], start=1):
        prev = previous_tags.get(tag_name, {})
        prev_score = prev.get("heat_score", 0)
        if prev_score > 0:
            trend_change = round((data["heat_score"] - prev_score) / prev_score * 100, 1)
        else:
            trend_change = 100.0  # new topic
        if trend_change > 10:
            trend = "rising"
        elif trend_change < -10:
            trend = "falling"
        else:
            trend = "stable"
        items.append({
            "rank": rank,
            "name": tag_name,
            "post_count": data["post_count"],
            "heat_score": data["heat_score"],
            "total_views": data["total_views"],
            "total_likes": data["total_likes"],
            "total_comments": data["total_comments"],
            "total_collects": data["total_collects"],
            "trend": trend,
            "trend_change": trend_change,
        })

    all_posts = db.query(Post).filter(
        Post.status == PostStatus.PUBLISHED,
        Post.created_at >= cutoff,
        Post.created_at <= now,
    ).count()
    avg_heat = round(sum(i["heat_score"] for i in items) / max(len(items), 1), 1)

    return ApiResponse(code=200, message="success", data={
        "period": period,
        "generated_at": now.isoformat(),
        "items": items,
        "summary": {
            "total_topics": len(current_tags),
            "total_posts": all_posts,
            "avg_heat_score": avg_heat,
        },
    })


@router.get("/admin/stats/engagement")
def engagement_report(
    period: str = Query("weekly", pattern="^(daily|weekly|monthly)$"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """用户参与度报告：活跃度概览、每日趋势、贡献者排行、参与度分布"""
    days_map = {"daily": 1, "weekly": 7, "monthly": 30}
    days = days_map[period]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now - timedelta(days=days)
    start = cutoff

    # --- Overview ---
    total_users = db.query(User).filter(User.status == UserStatus.ACTIVE).count()

    active_sets = [
        set(r[0] for r in db.query(Post.user_id).filter(
            Post.created_at >= cutoff, Post.status == PostStatus.PUBLISHED
        ).distinct().all()),
        set(r[0] for r in db.query(Comment.user_id).filter(
            Comment.created_at >= cutoff, Comment.status == CommentStatus.PUBLISHED
        ).distinct().all()),
        set(r[0] for r in db.query(Like.user_id).filter(
            Like.created_at >= cutoff
        ).distinct().all()),
    ]
    active_user_ids = active_sets[0] | active_sets[1] | active_sets[2]
    active_users = len(active_user_ids)

    new_users = db.query(User).filter(
        User.created_at >= cutoff, User.status == UserStatus.ACTIVE
    ).count()

    total_posts_period = db.query(Post).filter(
        Post.created_at >= cutoff, Post.status == PostStatus.PUBLISHED
    ).count()
    total_comments_period = db.query(Comment).filter(
        Comment.created_at >= cutoff, Comment.status == CommentStatus.PUBLISHED
    ).count()

    engagement_rate = round(active_users / max(total_users, 1) * 100, 1)
    avg_posts = round(total_posts_period / max(active_users, 1), 1)
    avg_comments = round(total_comments_period / max(active_users, 1), 1)

    overview = {
        "total_users": total_users,
        "active_users": active_users,
        "new_users": new_users,
        "engagement_rate": engagement_rate,
        "avg_posts_per_user": avg_posts,
        "avg_comments_per_user": avg_comments,
        "total_posts": total_posts_period,
        "total_comments": total_comments_period,
    }

    # --- Daily breakdown ---
    daily_breakdown = []
    total_period_days = (now - start).days + 1
    for offset in range(total_period_days):
        current = start + timedelta(days=offset)
        key = current.isoformat()
        daily_active = set(
            r[0] for r in db.query(Post.user_id).filter(
                func.date(Post.created_at) == key, Post.status == PostStatus.PUBLISHED
            ).distinct().all()
        ) | set(
            r[0] for r in db.query(Comment.user_id).filter(
                func.date(Comment.created_at) == key, Comment.status == CommentStatus.PUBLISHED
            ).distinct().all()
        ) | set(
            r[0] for r in db.query(Like.user_id).filter(
                func.date(Like.created_at) == key
            ).distinct().all()
        )
        daily_breakdown.append({
            "date": key,
            "active_users": len(daily_active),
            "new_posts": db.query(Post).filter(
                func.date(Post.created_at) == key, Post.status == PostStatus.PUBLISHED
            ).count(),
            "new_comments": db.query(Comment).filter(
                func.date(Comment.created_at) == key, Comment.status == CommentStatus.PUBLISHED
            ).count(),
            "new_likes": db.query(Like).filter(
                func.date(Like.created_at) == key
            ).count(),
        })

    # --- Top contributors ---
    post_counts = dict(
        db.query(Post.user_id, func.count(Post.id))
        .filter(Post.created_at >= cutoff, Post.status == PostStatus.PUBLISHED)
        .group_by(Post.user_id).all()
    )
    comment_counts = dict(
        db.query(Comment.user_id, func.count(Comment.id))
        .filter(Comment.created_at >= cutoff, Comment.status == CommentStatus.PUBLISHED)
        .group_by(Comment.user_id).all()
    )
    likes_received = dict(
        db.query(Post.user_id, func.count(Like.id))
        .join(Like, (Like.target_type == "post") & (Like.target_id == Post.id))
        .filter(Post.created_at >= cutoff, Post.status == PostStatus.PUBLISHED)
        .group_by(Post.user_id).all()
    )

    all_contributor_ids = set(post_counts) | set(comment_counts)
    contributors = []
    for uid in all_contributor_ids:
        pc = post_counts.get(uid, 0)
        cc = comment_counts.get(uid, 0)
        contributors.append({
            "user_id": uid,
            "posts_count": pc,
            "comments_count": cc,
            "likes_received": likes_received.get(uid, 0),
            "total_contributions": pc + cc,
        })
    contributors.sort(key=lambda c: c["total_contributions"], reverse=True)
    top_contributors = contributors[:20]

    # Resolve user names for top contributors
    top_user_ids = [c["user_id"] for c in top_contributors]
    user_map = {
        u.id: u
        for u in db.query(User).filter(User.id.in_(top_user_ids)).all()
    }
    top_contributors_ranked = []
    for rank, c in enumerate(top_contributors, start=1):
        u = user_map.get(c["user_id"])
        top_contributors_ranked.append({
            "rank": rank,
            "user_id": c["user_id"],
            "nickname": u.nickname if u else "未知用户",
            "avatar_url": u.avatar_url if u else None,
            "posts_count": c["posts_count"],
            "comments_count": c["comments_count"],
            "likes_received": c["likes_received"],
            "total_contributions": c["total_contributions"],
            "auth_level": u.auth_level.value if u else "basic",
        })

    # --- Engagement distribution ---
    high_count = sum(1 for c in contributors if c["total_contributions"] > 20)
    medium_count = sum(1 for c in contributors if 5 <= c["total_contributions"] <= 20)
    low_count = sum(1 for c in contributors if 1 <= c["total_contributions"] < 5)
    total_active_contributors = max(len(contributors), 1)

    engagement_distribution = {
        "high": {
            "count": high_count,
            "threshold": ">20",
            "percentage": round(high_count / total_active_contributors * 100, 1),
        },
        "medium": {
            "count": medium_count,
            "threshold": "5-20",
            "percentage": round(medium_count / total_active_contributors * 100, 1),
        },
        "low": {
            "count": low_count,
            "threshold": "1-4",
            "percentage": round(low_count / total_active_contributors * 100, 1),
        },
    }

    return ApiResponse(code=200, message="success", data={
        "overview": overview,
        "daily_breakdown": daily_breakdown,
        "top_contributors": top_contributors_ranked,
        "engagement_distribution": engagement_distribution,
    })


@router.get("/admin/categories")
def list_categories_for_admin(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    """管理员获取全量板块列表（含已隐藏的）。"""
    categories = db.query(Category).order_by(Category.sort_order, Category.id).all()
    return ApiResponse(code=200, message="success", data=[
        {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "sort_order": item.sort_order,
            "is_active": item.is_active,
            "post_count": item.post_count,
        }
        for item in categories
    ])


@router.post("/admin/categories", status_code=201)
def create_category(data: CategoryRequest, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    if db.query(Category).filter(Category.name == data.name).first():
        raise HTTPException(status_code=409, detail="板块名称已存在")
    category = Category(**data.model_dump())
    db.add(category)
    db.commit()
    return ApiResponse(code=201, message="板块创建成功", data={"id": category.id})


@router.put("/admin/categories/{category_id}")
def update_category(category_id: int, data: CategoryRequest, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="板块不存在")
    duplicate = db.query(Category).filter(Category.name == data.name, Category.id != category_id).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="板块名称已存在")
    for key, value in data.model_dump().items():
        setattr(category, key, value)
    db.commit()
    return ApiResponse(code=200, message="板块编辑成功", data={"id": category.id})


@router.delete("/admin/categories/{category_id}", status_code=204)
def delete_category(category_id: int, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="板块不存在")
    if category.post_count > 0:
        category.is_active = False
    else:
        db.delete(category)
    db.commit()
    return Response(status_code=204)


@router.get("/admin/reports")
def list_reports(
    status: str | None = Query(None, pattern="^(pending|resolved|dismissed)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Report)
    if status:
        query = query.filter(Report.status == ReportStatus(status))
    total = query.count()
    reports = query.order_by(Report.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return ApiResponse(code=200, message="success", data={
        "items": [
            {
                "id": item.id, "reporter_id": item.reporter_id, "target_type": item.target_type.value,
                "target_id": item.target_id, "reason": item.reason.value, "description": item.description,
                "status": item.status.value, "handle_comment": item.handle_comment, "created_at": item.created_at,
            }
            for item in reports
        ],
        "total": total, "page": page, "size": size,
    })


@router.post("/admin/reports/{report_id}")
def handle_report(
    report_id: int,
    data: ReportHandleRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="举报记录不存在")
    report.status = ReportStatus.RESOLVED if data.action == "resolve" else ReportStatus.DISMISSED
    report.handler_id = admin.id
    report.handle_comment = data.comment
    report.handled_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return ApiResponse(code=200, message="举报处理完成", data={"status": report.status.value})


@router.get("/admin/certifications")
def list_certifications(
    status: str = Query("pending", pattern="^(pending|approved|rejected)$"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    items = db.query(Certification).filter(Certification.status == CertificationStatus(status)).order_by(Certification.created_at).all()
    return ApiResponse(code=200, message="success", data=[
        {"id": item.id, "user_id": item.user_id, "real_name": item.real_name, "status": item.status.value, "created_at": item.created_at}
        for item in items
    ])


@router.post("/admin/certifications/{certification_id}/review")
def review_certification(
    certification_id: int,
    data: CertificationReviewRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    cert = db.query(Certification).filter(Certification.id == certification_id).first()
    if cert is None:
        raise HTTPException(status_code=404, detail="认证申请不存在")
    cert.status = CertificationStatus.APPROVED if data.action == "approve" else CertificationStatus.REJECTED
    cert.reviewer_id = admin.id
    cert.review_comment = data.comment
    cert.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if cert.status == CertificationStatus.APPROVED:
        user = db.query(User).filter(User.id == cert.user_id).first()
        user.auth_level = AuthLevel.VERIFIED
    db.commit()
    return ApiResponse(code=200, message="认证审核完成", data={"status": cert.status.value})


# ==================== 专业认证审核 ====================


@router.get("/admin/professional-certifications")
def list_professional_certifications(
    status: str = Query("pending", pattern="^(pending|approved|rejected)$"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    items = (
        db.query(ProfessionalCertification)
        .filter(ProfessionalCertification.status == ProfessionalCertStatus(status))
        .order_by(ProfessionalCertification.created_at)
        .all()
    )
    return ApiResponse(code=200, message="success", data=[
        {
            "id": item.id,
            "user_id": item.user_id,
            "qualification_docs": item.qualification_docs or [],
            "description": item.description,
            "status": item.status.value,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in items
    ])


@router.post("/admin/professional-certifications/{cert_id}/review")
def review_professional_certification(
    cert_id: int,
    data: CertificationReviewRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    cert = db.query(ProfessionalCertification).filter(ProfessionalCertification.id == cert_id).first()
    if cert is None:
        raise HTTPException(status_code=404, detail="专业认证申请不存在")
    cert.status = ProfessionalCertStatus.APPROVED if data.action == "approve" else ProfessionalCertStatus.REJECTED
    cert.reviewer_id = admin.id
    cert.review_comment = data.comment
    cert.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if cert.status == ProfessionalCertStatus.APPROVED:
        user = db.query(User).filter(User.id == cert.user_id).first()
        if user:
            user.auth_level = AuthLevel.PROFESSIONAL
            user.is_professional = True
    db.commit()
    return ApiResponse(code=200, message="专业认证审核完成", data={"status": cert.status.value})


@router.get("/admin/sensitive-words")
def list_sensitive_words(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    words = db.query(SensitiveWord).order_by(SensitiveWord.created_at.desc()).all()
    return ApiResponse(code=200, message="success", data=[
        {"id": item.id, "word": item.word, "level": item.level.value, "category": item.category, "is_active": item.is_active}
        for item in words
    ])


@router.post("/admin/sensitive-words", status_code=201)
def create_sensitive_word(data: SensitiveWordRequest, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    if db.query(SensitiveWord).filter(SensitiveWord.word == data.word).first():
        raise HTTPException(status_code=409, detail="敏感词已存在")
    item = SensitiveWord(word=data.word, level=SensitiveLevel(data.level), category=data.category, is_active=data.is_active)
    db.add(item)
    db.commit()
    return ApiResponse(code=201, message="添加成功", data={"id": item.id})


@router.delete("/admin/sensitive-words/{word_id}", status_code=204)
def delete_sensitive_word(word_id: int, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = db.query(SensitiveWord).filter(SensitiveWord.id == word_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="敏感词不存在")
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@router.get("/admin/activity-logs")
def activity_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: int | None = Query(None, ge=1),
    activity_type: str | None = Query(None, pattern="^(login|post|comment|like|follow|unfollow|share|vote)$"),
    start_date: date | None = None,
    end_date: date | None = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(UserActivityLog)
    if user_id:
        query = query.filter(UserActivityLog.user_id == user_id)
    if activity_type:
        query = query.filter(UserActivityLog.activity_type == ActivityType(activity_type))
    if start_date:
        query = query.filter(UserActivityLog.created_at >= start_date)
    if end_date:
        query = query.filter(UserActivityLog.created_at <= end_date + timedelta(days=1))
    total = query.count()
    logs = query.order_by(UserActivityLog.created_at.desc()).offset((page - 1) * size).limit(size).all()
    # Resolve user nicknames for the current page
    uids = list({log.user_id for log in logs})
    user_map = {u.id: u.nickname for u in db.query(User).filter(User.id.in_(uids)).all()} if uids else {}
    return ApiResponse(code=200, message="success", data={
        "items": [
            {"id": item.id, "user_id": item.user_id,
             "user_nickname": user_map.get(item.user_id),
             "activity_type": item.activity_type.value,
             "target_type": item.target_type, "target_id": item.target_id,
             "created_at": item.created_at}
            for item in logs
        ],
        "total": total, "page": page, "size": size,
    })


# ── 合规检查 ──


@router.post("/admin/compliance/check")
def compliance_check(
    data: ComplianceCheckRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """手动对一段文本运行合规检查，返回匹配结果。"""
    result = check_compliance_single_text(db, data.text)
    return ApiResponse(code=200, message="success", data={
        "level": result.level.value if result.level else None,
        "should_block": result.should_block,
        "should_review": result.should_review,
        "matches": [
            {
                "rule_id": m.rule_id,
                "rule_name": m.rule_name,
                "category": m.category.value,
                "severity": m.severity.value,
                "matched_text": m.matched_text,
                "description": m.description,
            }
            for m in result.matches
        ],
        "categories": result.categories,
    })


@router.get("/admin/compliance/rules")
def list_compliance_rules(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """列出所有合规检查规则。"""
    rules = db.query(ComplianceRule).order_by(ComplianceRule.created_at.desc()).all()
    return ApiResponse(code=200, message="success", data=[
        {
            "id": r.id,
            "name": r.name,
            "category": r.category.value,
            "pattern": r.pattern,
            "severity": r.severity.value,
            "description": r.description,
            "is_active": r.is_active,
            "created_at": r.created_at,
        }
        for r in rules
    ])


@router.post("/admin/compliance/rules", status_code=201)
def create_compliance_rule(
    data: ComplianceRuleCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """创建一条新的合规检查规则。"""
    # 校验正则表达式有效性
    try:
        re.compile(data.pattern)
    except re.error as e:
        raise HTTPException(status_code=400, detail=f"正则表达式无效: {e.msg}")
    rule = ComplianceRule(
        name=data.name,
        category=ComplianceCategory(data.category),
        pattern=data.pattern,
        severity=SensitiveLevel(data.severity),
        description=data.description,
    )
    db.add(rule)
    db.commit()
    return ApiResponse(code=201, message="合规规则创建成功", data={"id": rule.id})


@router.delete("/admin/compliance/rules/{rule_id}", status_code=204)
def delete_compliance_rule(
    rule_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """删除一条合规检查规则。"""
    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="合规规则不存在")
    db.delete(rule)
    db.commit()
    return Response(status_code=204)


# ── 重复内容检测 ──


@router.post("/admin/duplicate-content/scan")
def scan_duplicate_content(
    data: DuplicateScanRequest = DuplicateScanRequest(),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """扫描重复内容。支持按文本或时间范围扫描。"""
    text = data.text
    start_date = data.start_date
    end_date = data.end_date
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
    if start_date:
        cutoff = start_date
    end = end_date or date.today()
    end_dt = datetime(end.year, end.month, end.day) + timedelta(days=1)

    posts = db.query(Post).filter(
        Post.created_at >= cutoff,
        Post.created_at <= end_dt,
        Post.status.in_([PostStatus.PUBLISHED, PostStatus.REVIEWING]),
    ).order_by(Post.created_at.desc()).limit(500).all()

    pairs = []
    if text and text.strip():
        from difflib import SequenceMatcher
        from app.services.duplicate_content_service import _normalize_text
        normalized_input = _normalize_text(text, text)
        for post in posts:
            normalized_post = _normalize_text(post.title, post.content)
            if len(normalized_input) < 20 or len(normalized_post) < 20:
                continue
            sim = round(SequenceMatcher(None, normalized_input, normalized_post).ratio(), 4)
            if sim >= 0.80:
                pairs.append({
                    "source_post_id": None,
                    "source_title": "输入文本",
                    "source_author": None,
                    "matched_post_id": post.id,
                    "matched_title": post.title[:100],
                    "matched_author": {"id": post.author.id, "nickname": post.author.nickname} if post.author else None,
                    "similarity": sim,
                    "status": "exact_duplicate" if sim >= 0.99 else "near_duplicate",
                })
    else:
        from difflib import SequenceMatcher
        from app.services.duplicate_content_service import _normalize_text
        posts_by_user: dict[int, list] = {}
        for post in posts:
            posts_by_user.setdefault(post.user_id, []).append(post)
        for uid, user_posts in posts_by_user.items():
            for i in range(len(user_posts)):
                for j in range(i + 1, len(user_posts)):
                    a, b = user_posts[i], user_posts[j]
                    na = _normalize_text(a.title, a.content)
                    nb = _normalize_text(b.title, b.content)
                    if len(na) < 20 or len(nb) < 20:
                        continue
                    sim = round(SequenceMatcher(None, na, nb).ratio(), 4)
                    if sim >= 0.80:
                        pairs.append({
                            "source_post_id": a.id,
                            "source_title": a.title[:100],
                            "source_author": {"id": a.author.id, "nickname": a.author.nickname} if a.author else None,
                            "matched_post_id": b.id,
                            "matched_title": b.title[:100],
                            "matched_author": {"id": b.author.id, "nickname": b.author.nickname} if b.author else None,
                            "similarity": sim,
                            "status": "exact_duplicate" if sim >= 0.99 else "near_duplicate",
                        })

    pairs.sort(key=lambda p: p["similarity"], reverse=True)
    return ApiResponse(code=200, message="扫描完成", data={
        "total_posts_scanned": len(posts),
        "pairs": pairs[:50],
        "scanned_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
    })


@router.get("/admin/duplicate-content/stats")
def duplicate_content_stats(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """重复内容检测统计数据。"""
    total_blocked = db.query(Post).filter(Post.status == PostStatus.REJECTED).count()
    total_flagged = db.query(Post).filter(Post.status == PostStatus.REVIEWING).count()

    recent = db.query(Post).filter(
        Post.status.in_([PostStatus.PUBLISHED, PostStatus.REVIEWING]),
    ).order_by(Post.created_at.desc()).limit(100).all()

    exact, high_sim, med_sim = 0, 0, 0
    from difflib import SequenceMatcher
    from app.services.duplicate_content_service import _normalize_text
    posts_by_user: dict[int, list] = {}
    for post in recent:
        posts_by_user.setdefault(post.user_id, []).append(post)
    for uid, user_posts in posts_by_user.items():
        for i in range(len(user_posts)):
            for j in range(i + 1, len(user_posts)):
                a, b = user_posts[i], user_posts[j]
                na = _normalize_text(a.title, a.content)
                nb = _normalize_text(b.title, b.content)
                if len(na) < 20 or len(nb) < 20:
                    continue
                sim = SequenceMatcher(None, na, nb).ratio()
                if sim >= 0.99:
                    exact += 1
                elif sim >= 0.95:
                    high_sim += 1
                elif sim >= 0.92:
                    med_sim += 1

    return ApiResponse(code=200, message="success", data={
        "total_blocked": total_blocked,
        "total_flagged": total_flagged,
        "recent_posts_scanned": len(recent),
        "by_similarity": {
            "exact_duplicates": exact,
            "near_duplicates_95_100": high_sim,
            "near_duplicates_92_95": med_sim,
        },
    })


# ── 用户行为监控 ──


@router.get("/admin/behavior/user-summary")
def user_behavior_summary(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    sort_by: str = Query("total_actions", pattern="^(total_actions|posts_count|comments_count|last_active|account_age)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """按用户聚合的活动统计，支持排序和分页。"""
    post_subq = (
        db.query(Post.user_id, func.count(Post.id).label("post_count"))
        .group_by(Post.user_id).subquery()
    )
    comment_subq = (
        db.query(Comment.user_id, func.count(Comment.id).label("comment_count"))
        .group_by(Comment.user_id).subquery()
    )
    like_subq = (
        db.query(Like.user_id, func.count(Like.id).label("like_count"))
        .group_by(Like.user_id).subquery()
    )
    activity_subq = (
        db.query(
            UserActivityLog.user_id,
            func.count(UserActivityLog.id).label("total_actions"),
            func.max(UserActivityLog.created_at).label("last_active_at"),
        )
        .group_by(UserActivityLog.user_id).subquery()
    )

    query = (
        db.query(
            User.id.label("user_id"),
            User.nickname,
            User.avatar_url,
            User.created_at.label("account_created_at"),
            User.status,
            func.coalesce(post_subq.c.post_count, 0).label("posts_count"),
            func.coalesce(comment_subq.c.comment_count, 0).label("comments_count"),
            func.coalesce(like_subq.c.like_count, 0).label("likes_count"),
            func.coalesce(activity_subq.c.total_actions, 0).label("total_actions"),
            activity_subq.c.last_active_at,
        )
        .outerjoin(post_subq, User.id == post_subq.c.user_id)
        .outerjoin(comment_subq, User.id == comment_subq.c.user_id)
        .outerjoin(like_subq, User.id == like_subq.c.user_id)
        .outerjoin(activity_subq, User.id == activity_subq.c.user_id)
    )

    sort_col = {
        "total_actions": func.coalesce(activity_subq.c.total_actions, 0),
        "posts_count": func.coalesce(post_subq.c.post_count, 0),
        "comments_count": func.coalesce(comment_subq.c.comment_count, 0),
        "last_active": func.coalesce(activity_subq.c.last_active_at, datetime(2000, 1, 1)),
        "account_age": User.created_at,
    }[sort_by]
    order_fn = desc if sort_order == "desc" else sort_col
    query = query.order_by(order_fn(sort_col))

    total = query.count()
    rows = query.offset((page - 1) * size).limit(size).all()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    items = []
    for row in rows:
        age_days = max(1, (now - row.account_created_at).days) if row.account_created_at else 1
        items.append({
            "user_id": row.user_id,
            "nickname": row.nickname,
            "avatar_url": row.avatar_url,
            "total_actions": row.total_actions,
            "posts_count": row.posts_count,
            "comments_count": row.comments_count,
            "likes_count": row.likes_count,
            "last_active_at": row.last_active_at.isoformat() if row.last_active_at else None,
            "account_age_days": age_days,
            "posting_frequency": round(row.posts_count / (age_days / 7), 2) if age_days else 0,
            "status": row.status.value,
        })

    return ApiResponse(code=200, message="success", data={
        "items": items, "total": total, "page": page, "size": size,
    })


@router.get("/admin/behavior/user/{user_id}/timeline")
def user_activity_timeline(
    user_id: int,
    days: int = Query(7, ge=1, le=90),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """单个用户的活动时间线。"""
    target = db.query(User).filter(User.id == user_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    logs = (
        db.query(UserActivityLog)
        .filter(UserActivityLog.user_id == user_id, UserActivityLog.created_at >= cutoff)
        .order_by(UserActivityLog.created_at.desc())
        .all()
    )

    from collections import defaultdict
    daily: dict[str, dict] = defaultdict(lambda: {"login": 0, "post": 0, "comment": 0, "like": 0, "other": 0})
    for log in logs:
        date_key = log.created_at.date().isoformat()
        atype = log.activity_type.value
        if atype in ("login", "post", "comment", "like"):
            daily[date_key][atype] += 1
        else:
            daily[date_key]["other"] += 1

    # 计算用户近期帖子质量评分
    from app.services.quality_service import score_content
    recent_posts = (
        db.query(Post)
        .filter(Post.user_id == user_id, Post.created_at >= cutoff)
        .order_by(Post.created_at.desc()).limit(20).all()
    )
    quality_scores = []
    for p in recent_posts:
        qs = score_content(p.content)
        quality_scores.append({
            "post_id": p.id,
            "title": p.title[:80],
            "score": qs.score,
            "level": qs.level,
            "flags": qs.flags,
            "word_count": qs.word_count,
            "char_count": qs.char_count,
        })
    avg_quality = round(sum(s["score"] for s in quality_scores) / max(len(quality_scores), 1), 1)

    return ApiResponse(code=200, message="success", data={
        "user": {
            "id": target.id, "nickname": target.nickname,
            "avatar_url": target.avatar_url, "status": target.status.value,
            "created_at": target.created_at.isoformat() if target.created_at else None,
        },
        "timeline": [
            {"date": key, **counts} for key, counts in sorted(daily.items())
        ],
        "recent_activities": [
            {
                "id": log.id, "activity_type": log.activity_type.value,
                "target_type": log.target_type, "target_id": log.target_id,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs[:50]
        ],
        "quality": {
            "avg_score": avg_quality,
            "posts_scored": len(quality_scores),
            "details": quality_scores,
        },
    })


@router.get("/admin/behavior/suspicious")
def suspicious_behavior(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """检测异常用户行为。"""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff_24h = now - timedelta(hours=24)
    cutoff_7d = now - timedelta(days=7)

    suspicious = []

    high_freq = (
        db.query(Post.user_id, func.count(Post.id).label("cnt"))
        .filter(Post.created_at >= cutoff_24h)
        .group_by(Post.user_id)
        .having(func.count(Post.id) > 20).all()
    )
    for uid, cnt in high_freq:
        suspicious.append({"user_id": uid, "pattern": "high_frequency_posting",
                           "detail": f"24小时内发帖{cnt}次", "severity": "high"})

    new_active = (
        db.query(UserActivityLog.user_id, func.count(UserActivityLog.id).label("cnt"))
        .join(User, UserActivityLog.user_id == User.id)
        .filter(User.created_at >= cutoff_7d, UserActivityLog.created_at >= cutoff_24h)
        .group_by(UserActivityLog.user_id)
        .having(func.count(UserActivityLog.id) > 50).all()
    )
    for uid, cnt in new_active:
        suspicious.append({"user_id": uid, "pattern": "new_account_high_activity",
                           "detail": f"注册不足7天，24小时内操作{cnt}次", "severity": "medium"})

    multi_ban = (
        db.query(BanRecord.user_id, func.count(BanRecord.id).label("cnt"))
        .filter(BanRecord.action == BanAction.BAN)
        .group_by(BanRecord.user_id)
        .having(func.count(BanRecord.id) >= 3).all()
    )
    for uid, cnt in multi_ban:
        suspicious.append({"user_id": uid, "pattern": "multiple_bans",
                           "detail": f"已被封禁{cnt}次", "severity": "high"})

    uids = list({s["user_id"] for s in suspicious})
    user_map = {u.id: u for u in db.query(User).filter(User.id.in_(uids)).all()} if uids else {}

    merged: dict[int, list] = {}
    for s in suspicious:
        merged.setdefault(s["user_id"], []).append(s)

    items = []
    for uid, entries in merged.items():
        u = user_map.get(uid)
        for e in entries:
            items.append({
                "user_id": uid,
                "nickname": u.nickname if u else "未知",
                "avatar_url": u.avatar_url if u else None,
                "pattern": e["pattern"],
                "detail": e["detail"],
                "severity": e["severity"],
            })

    items.sort(key=lambda x: {"high": 0, "medium": 1}[x["severity"]])

    # 为高风险项自动生成管理员告警（去重：同一用户+同一模式24h内不重复）
    recent_cutoff = now - timedelta(hours=24)
    for entry in items:
        if entry["severity"] != "high":
            continue
        existing = db.query(Notification).filter(
            Notification.type == NotificationType.SYSTEM_ALERT,
            Notification.target_type == entry["pattern"],
            Notification.target_id == entry["user_id"],
            Notification.created_at >= recent_cutoff,
        ).first()
        if not existing:
            _create_admin_alert(
                db, title=f"异常行为告警: {entry['nickname']}",
                content=entry["detail"],
                target_type=entry["pattern"],
                target_id=entry["user_id"],
            )
    db.commit()

    return ApiResponse(code=200, message="success", data={"items": items, "total": len(items)})
