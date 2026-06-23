from typing import Literal

from pydantic import BaseModel, Field, model_validator


class GroupPostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    content: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list, max_length=10)


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: str | None = Field(None, max_length=500)
    avatar_url: str | None = Field(None, max_length=500)
    visibility: Literal["public", "private"] = "public"
    need_approval: bool = False


class GroupUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=50)
    description: str | None = Field(None, max_length=500)
    avatar_url: str | None = Field(None, max_length=500)
    visibility: Literal["public", "private"] | None = None
    need_approval: bool | None = None


class MemberReview(BaseModel):
    user_id: int
    action: Literal["approve", "reject"]


class MessageCreate(BaseModel):
    receiver_id: int | None = Field(None, description="私信接收者（与 group_id 二选一）")
    group_id: int | None = Field(None, description="群组 ID（与 receiver_id 二选一）")
    content: str = Field(..., min_length=1, max_length=5000)
    message_type: Literal["text", "image", "file"] = "text"
    attachment_url: str | None = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_target(self):
        if self.receiver_id and self.group_id:
            raise ValueError("不能同时指定接收者和群组")
        if not self.receiver_id and not self.group_id:
            raise ValueError("必须指定接收者或群组")
        if self.message_type in ("image", "file") and not self.attachment_url:
            raise ValueError("图片或文件消息必须提供附件地址")
        return self
