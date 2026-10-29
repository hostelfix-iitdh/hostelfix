from pydantic import BaseModel, ConfigDict
class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
class HostelOut(ORMModel):
    id: int
    name: str
class FloorOut(ORMModel):
    id: int
    hostel_id: int
    floor_number: int
class WingOut(ORMModel):
    id: int
    floor_id: int
    wing_name: str
class LocationOut(ORMModel):
    id: int
    wing_id: int
    area_type: str
    description: str | None
class CategoryOut(ORMModel):
    id: int
    name: str
    description: str | None
class ProblemTypeOut(ORMModel):
    id: int
    category_id: int
    name: str
    description: str | None
    requires_description: bool
class AssetOut(ORMModel):
    id: int
    name: str
    asset_type: str
    description: str | None
