from datetime import datetime
from pydantic import BaseModel, Field
from typing import List


class GroupBase(BaseModel):
    """Base group schema."""
    name: str = Field(..., min_length=1, max_length=255)


class GroupCreate(GroupBase):
    """Schema for creating a group."""
    pass


class GroupResponse(GroupBase):
    """Schema for group response."""
    id: str
    created_at: datetime
    user_count: int = 0

    class Config:
        from_attributes = True


class GroupMemberAdd(BaseModel):
    """Schema for adding a member to a group."""
    user_id: str
