from typing import Literal

from pydantic import BaseModel, Field


class PrivacySettingsSchema(BaseModel):
    """用户隐私设置 — 控制个人资料、私信、关注列表等可见范围。"""

    profile_visibility: Literal["public", "followers_only", "private"] = Field(
        "public", description="个人资料可见范围"
    )
    message_permission: Literal["everyone", "followers_only", "none"] = Field(
        "everyone", description="谁可以给我发私信"
    )
    show_investment_info: bool = Field(
        True, description="是否公开投资标签和风险偏好"
    )
    show_follow_lists: bool = Field(
        True, description="是否公开关注/粉丝列表"
    )
    show_activity_status: bool = Field(
        True, description="是否公开活动状态"
    )
