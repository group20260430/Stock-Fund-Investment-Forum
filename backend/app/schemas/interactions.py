from typing import Literal

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: int | None = None
    reply_to_id: int | None = None


class CollectRequest(BaseModel):
    folder_name: str = Field("默认收藏夹", min_length=1, max_length=50)


class ShareRequest(BaseModel):
    share_type: Literal["timeline", "message", "group"] = "timeline"
    comment: str | None = Field(None, max_length=500)
