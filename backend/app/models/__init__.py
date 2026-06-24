from app.db.base import Base
from app.models.user import User
from app.models.certification import Certification, CertificationStatus
from app.models.refresh_token import RefreshToken
from app.models.risk_assessment import RiskAssessment, RiskLevelEnum

__all__ = [
    "Base",
    "User",
    "Certification",
    "CertificationStatus",
    "RefreshToken",
    "RiskAssessment",
    "RiskLevelEnum",
]
"""Import every ORM model so Base.metadata is complete for scripts and tests."""

from app.models.certification import Certification
from app.models.community import Group, GroupMember, GroupPost, Message
from app.models.notification import Notification, NotificationType
from app.models.content import (
    Attachment,
    Category,
    Comment,
    Favorite,
    FavoriteFolder,
    Like,
    Post,
    Share,
    VoteOption,
    VoteRecord,
)
from app.models.operations import (
    BanRecord,
    DailyStat,
    Report,
    ReviewLog,
    SensitiveWord,
    UserActivityLog,
)
from app.models.oauth import OAuthAccount, OAuthProvider
from app.models.points import PointsHistory
from app.models.professional_certification import ProfessionalCertification, ProfessionalCertStatus
from app.models.refresh_token import RefreshToken
from app.models.risk_assessment import RiskAssessment
from app.models.social import Follow, StarredUser
from app.models.user import User

__all__ = [
    "Attachment",
    "BanRecord",
    "Category",
    "Certification",
    "Comment",
    "DailyStat",
    "Favorite",
    "FavoriteFolder",
    "Follow",
    "Group",
    "GroupMember",
    "GroupPost",
    "Like",
    "Message",
    "Notification",
    "NotificationType",
    "OAuthAccount",
    "OAuthProvider",
    "PointsHistory",
    "Post",
    "ProfessionalCertification",
    "ProfessionalCertStatus",
    "RefreshToken",
    "Report",
    "ReviewLog",
    "RiskAssessment",
    "SensitiveWord",
    "Share",
    "StarredUser",
    "User",
    "UserActivityLog",
    "VoteOption",
    "VoteRecord",
]
