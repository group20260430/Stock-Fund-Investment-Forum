from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AttachmentInput(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=255)
    file_url: str = Field(..., min_length=1, max_length=500)
    file_size: int = Field(0, ge=0, le=10 * 1024 * 1024)
    file_type: str = Field("application/octet-stream", max_length=100)


class VoteOptionInput(BaseModel):
    label: str = Field(..., min_length=1, max_length=200)


class PostCreate(BaseModel):
    category_id: int
    title: str = Field(..., min_length=1, max_length=120)
    content: str = Field(..., min_length=1)
    post_type: Literal["normal", "long_article", "poll", "moment"] = "normal"
    status: Literal["draft", "published"] = "published"
    tags: list[str] = Field(default_factory=list, max_length=10)
    attachments: list[AttachmentInput] = Field(default_factory=list, max_length=10)
    vote_options: list[VoteOptionInput] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def validate_poll_options(self):
        if self.post_type == "poll" and len(self.vote_options) < 2:
            raise ValueError("投票帖至少需要2个选项")
        return self


class PostUpdate(PostCreate):
    pass


class VoteRequest(BaseModel):
    option_ids: list[int] = Field(..., min_length=1, max_length=10)
