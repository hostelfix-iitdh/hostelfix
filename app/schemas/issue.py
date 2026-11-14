from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class IssueCreate(BaseModel):
    title: str = Field(min_length=5, max_length=180)
    description: str = Field(min_length=10, max_length=5000)
    location_id: int = Field(gt=0)
    problem_type_id: int = Field(gt=0)
    asset_id: int | None = Field(default=None, gt=0)
    room_label: str | None = Field(default=None, max_length=80)
    service_date: date | None = None
    is_public: bool = True


class IssuePatch(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=180)
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    location_id: int | None = Field(default=None, gt=0)
    problem_type_id: int | None = Field(default=None, gt=0)
    asset_id: int | None = Field(default=None, gt=0)
    room_label: str | None = Field(default=None, max_length=80)
    service_date: date | None = None
    is_public: bool | None = None


class StatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(submitted|acknowledged|in_progress|resolved|closed|rejected|reopened)$"
    )
    comment: str | None = Field(default=None, max_length=2000)
    is_internal: bool = False


class ResolutionFeedbackCreate(BaseModel):
    outcome: str = Field(pattern="^(resolved|not_resolved|reopen_requested)$")
    comment: str | None = Field(default=None, max_length=2000)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class IssueOut(ORMModel):
    id: int
    title: str
    description: str
    location_id: int
    problem_type_id: int
    asset_id: int | None
    status: str
    service_date: date | None
    is_public: bool
    due_date: date | None
    created_at: datetime
    updated_at: datetime


class IssueUpdateOut(ORMModel):
    id: int
    issue_id: int
    old_status: str | None
    actor_role: str
    new_status: str
    comment: str | None
    created_at: datetime


class StaffIssueOut(IssueOut):
    room_label: str | None
