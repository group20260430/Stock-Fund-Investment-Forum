from datetime import date, datetime, timedelta, timezone
import re

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin, get_current_user
from app.db.session import get_db
from app.models.certification import Certification, CertificationStatus
from app.models.content import Category, Comment, CommentStatus, Like, Post, PostStatus, Share
from app.models.operations import (
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
    ReportCreate,
    ReportHandleRequest,
    ReviewRequest,
    SensitiveWordRequest,
)
from app.schemas.user import ApiResponse
from app.services.compliance_service import check_compliance_single_text

router = APIRouter(tags=["admin"])


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
    items = [
        {
            "id": f"post-{item.id}",
            "content_type": "post",
            "title": item.title,
            "author": {"id": item.author.id, "nickname": item.author.nickname},
            "flags": [],
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
            "flags": [],
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
    return ApiResponse(code=200, message="success", data={
        "daily_active_users": len(active_ids),
        "new_users_today": _today_count(db, User, User.created_at),
        "total_posts": db.query(Post).count(),
        "total_comments": db.query(Comment).count(),
        "pending_review": db.query(Post).filter(Post.status == PostStatus.REVIEWING).count()
        + db.query(Comment).filter(Comment.status == CommentStatus.REVIEWING).count(),
        "reports_today": _today_count(db, Report, Report.created_at),
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
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(UserActivityLog)
    total = query.count()
    logs = query.order_by(UserActivityLog.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return ApiResponse(code=200, message="success", data={
        "items": [
            {"id": item.id, "user_id": item.user_id, "activity_type": item.activity_type.value,
             "target_type": item.target_type, "target_id": item.target_id, "created_at": item.created_at}
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
