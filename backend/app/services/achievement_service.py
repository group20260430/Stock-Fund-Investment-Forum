"""Achievement service — calculate user badges and influence score.

Badge rules are based on user stats collected from the database.
Each badge has a unique ID, display name, description, and unlock condition.
"""

from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.models.content import Comment, Like, Post
from app.models.notification import Notification
from app.models.social import Follow
from app.models.community import GroupMember, Message
from app.models.user import AuthLevel, User
from app.schemas.user import Achievements

# ── Badge definitions ──────────────────────────────────────────────────────
#
# Each badge: (id, name, description)
# Conditions are checked in calculate_achievements() below.

BADGE_FIRST_POST = ("first_post", "初露锋芒", "发布第一篇帖子")
BADGE_10_POSTS = ("prolific_10", "笔耕不辍", "累计发帖达到10篇")
BADGE_50_POSTS = ("prolific_50", "论坛达人", "累计发帖达到50篇")
BADGE_100_POSTS = ("prolific_100", "意见领袖", "累计发帖达到100篇")
BADGE_ELITE_1 = ("elite_1", "精华大师", "获得1篇精华帖")
BADGE_ELITE_5 = ("elite_5", "精英作者", "获得5篇精华帖")
BADGE_LIKES_50 = ("likes_50", "人气新星", "获得50次点赞")
BADGE_LIKES_200 = ("likes_200", "万人迷", "获得200次点赞")
BADGE_FOLLOWERS_10 = ("followers_10", "社交达人", "粉丝数达到10人")
BADGE_FOLLOWERS_50 = ("followers_50", "网红", "粉丝数达到50人")
BADGE_COMMENTS_50 = ("comments_50", "评论家", "累计评论达到50条")
BADGE_RISK_ASSESSED = ("risk_assessed", "风险意识", "完成投资者风险评估")
BADGE_CERTIFIED = ("certified", "认证用户", "完成实名认证")
BADGE_PROFESSIONAL = ("professional", "专业人士", "获得专业认证（加V标识）")
BADGE_GROUP_CREATOR = ("group_creator", "群组创建者", "创建了一个投资群组")
BADGE_GROUP_ACTIVE = ("group_active", "社群活跃", "群聊消息达到20条")
BADGE_WARNED = ("warned", "需留意", "收到过违规警告（自我提醒）")


def calculate_achievements(db: Session, user: User) -> Achievements:
    """Calculate the user's achievements based on current database stats.

    Gathers counts from multiple tables and determines which badges
    the user has unlocked.  All queries are read-only.
    """
    # ── Core stats ────────────────────────────────────────────────────
    user_id = user.id

    # Post count (including all statuses)
    posts_count = db.query(sa_func.count(Post.id)).filter(
        Post.user_id == user_id
    ).scalar() or 0

    # Elite post count
    elite_posts = db.query(sa_func.count(Post.id)).filter(
        Post.user_id == user_id,
        Post.is_elite.is_(True),
    ).scalar() or 0

    # Total likes received on user's posts
    # Like uses polymorphic (target_type, target_id); find user's post IDs first
    user_post_ids = [row[0] for row in db.query(Post.id).filter(Post.user_id == user_id).all()]
    if user_post_ids:
        likes_received = db.query(sa_func.count(Like.id)).filter(
            Like.target_type == "post",
            Like.target_id.in_(user_post_ids),
        ).scalar() or 0
    else:
        likes_received = 0

    # Comment count
    comments_count = db.query(sa_func.count(Comment.id)).filter(
        Comment.user_id == user_id
    ).scalar() or 0

    # Group membership
    groups_created = db.query(sa_func.count(GroupMember.id)).filter(
        GroupMember.user_id == user_id,
        GroupMember.role == "owner",
    ).scalar() or 0

    group_messages = db.query(sa_func.count(Message.id)).filter(
        Message.sender_id == user_id,
        Message.group_id.isnot(None),
    ).scalar() or 0

    # Notification check for certification (simplified — checks auth_level)
    auth_level = user.auth_level

    # ── Collect badges ────────────────────────────────────────────────
    badges: list[str] = []

    # Post milestones
    if posts_count >= 1:
        badges.append(BADGE_FIRST_POST[0])
    if posts_count >= 10:
        badges.append(BADGE_10_POSTS[0])
    if posts_count >= 50:
        badges.append(BADGE_50_POSTS[0])
    if posts_count >= 100:
        badges.append(BADGE_100_POSTS[0])

    # Elite posts
    if elite_posts >= 1:
        badges.append(BADGE_ELITE_1[0])
    if elite_posts >= 5:
        badges.append(BADGE_ELITE_5[0])

    # Likes received
    if likes_received >= 50:
        badges.append(BADGE_LIKES_50[0])
    if likes_received >= 200:
        badges.append(BADGE_LIKES_200[0])

    # Followers
    followers_count = user.followers_count or 0
    if followers_count >= 10:
        badges.append(BADGE_FOLLOWERS_10[0])
    if followers_count >= 50:
        badges.append(BADGE_FOLLOWERS_50[0])

    # Comments
    if comments_count >= 50:
        badges.append(BADGE_COMMENTS_50[0])

    # Risk assessment completed
    if user.risk_level is not None:
        badges.append(BADGE_RISK_ASSESSED[0])

    # Certification
    if auth_level in (AuthLevel.VERIFIED, AuthLevel.PROFESSIONAL):
        badges.append(BADGE_CERTIFIED[0])

    # Professional (加V)
    if auth_level == AuthLevel.PROFESSIONAL or user.is_professional:
        badges.append(BADGE_PROFESSIONAL[0])

    # Group creator
    if groups_created >= 1:
        badges.append(BADGE_GROUP_CREATOR[0])

    # Group active
    if group_messages >= 20:
        badges.append(BADGE_GROUP_ACTIVE[0])

    # Received a warning
    warn_count = user.warn_count or 0
    if warn_count >= 1:
        badges.append(BADGE_WARNED[0])

    # ── Influence score ───────────────────────────────────────────────
    influence_score = (
        posts_count * 10
        + elite_posts * 50
        + likes_received * 2
        + followers_count * 5
        + comments_count * 3
    )

    return Achievements(
        posts_count=posts_count,
        elite_posts=elite_posts,
        influence_score=influence_score,
        badges=badges,
    )
