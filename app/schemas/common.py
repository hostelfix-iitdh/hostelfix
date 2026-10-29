from pydantic import BaseModel, ConfigDict, Field
from typing import Generic, TypeVar

T = TypeVar("T")
class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class PageMeta(BaseModel):
    page: int = Field(ge=1)
    size: int = Field(ge=1, le=50)
    total: int = Field(ge=0)

class ErrorBody(BaseModel):
    code: str
    message: str
    details: list | dict | None = None

class ErrorResponse(BaseModel):
    error: ErrorBody
