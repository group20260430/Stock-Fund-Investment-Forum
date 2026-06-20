from pydantic import BaseModel


class StarredRequest(BaseModel):
    user_id: int
    is_starred: bool
