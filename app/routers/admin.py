from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Issue, Category, ProblemType, User, Hostel, Floor, Wing, Location, Asset, AssetLocation, EmailToken
from app.routers.deps import require_role
from app.services.security import random_token, token_hash, expiry
from app.services.mailer import send_mail
from app.core.config import settings

router = APIRouter(tags=["Admin"])

class StaffCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    category_id: int = Field(gt=0)

class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    resolution_target_hours: int = Field(default=168, ge=1, le=8760)

class CategoryPatch(BaseModel):
    description: str | None = Field(default=None, max_length=255)
    resolution_target_hours: int | None = Field(default=None, ge=1, le=8760)

class ProblemTypeCreate(BaseModel):
    category_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    requires_description: bool = False

class ProblemTypePatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    requires_description: bool | None = None

class AssetCreate(BaseModel):
    hostel_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=120)
    asset_type: str = Field(min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    location_ids: list[int] = Field(default_factory=list)

class AssetPatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    asset_type: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=255)

class AssetLocationLink(BaseModel):
    location_id: int = Field(gt=0)

class HostelCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)

class FloorCreate(BaseModel):
    hostel_id: int = Field(gt=0)
    floor_number: int = Field(ge=0, le=100)

class WingCreate(BaseModel):
    floor_id: int = Field(gt=0)
    wing_name: str = Field(min_length=1, max_length=5)

class LocationCreate(BaseModel):
    wing_id: int = Field(gt=0)
    area_type: str = Field(min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=255)

class LocationPatch(BaseModel):
    area_type: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=255)

@router.post("/admin/staff", status_code=201)
def create_staff(payload: StaffCreate, actor: User = Depends(require_role("administrator")), db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    if db.query(User).filter(func.lower(User.email) == email).first():
        raise HTTPException(409, "An account with this email already exists")
    category = db.get(Category, payload.category_id)
    if not category:
        raise HTTPException(422, "Unknown category_id")
    user = User(name=payload.name.strip(), email=email, role="staff", category_id=category.id, is_verified=False)
    db.add(user); db.flush()
    raw = random_token()
    db.add(EmailToken(user_id=user.id, token_hash=token_hash(raw), purpose="set_password", expires_at=expiry(24*60)))
    db.commit(); db.refresh(user)
    link = f"{settings.cors_origin_list[0]}/?set-password={raw}"
    send_mail(email, "Set your HostelFix staff password", f"Open this link to set your password:\n{link}\n\nThis link expires in 24 hours.")
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "category_id": user.category_id,
            "development_set_password_url": link if settings.mail_mode == "log" else None}

@router.get("/admin/analytics")
def analytics(actor: User = Depends(require_role("administrator")), db: Session = Depends(get_db)):
    by_status = db.query(Issue.status, func.count(Issue.id)).group_by(Issue.status).all()
    by_category = (db.query(Category.name, func.count(Issue.id))
                   .join(ProblemType, ProblemType.category_id == Category.id)
                   .join(Issue, Issue.problem_type_id == ProblemType.id, isouter=True)
                   .group_by(Category.name).all())
    by_location = (db.query(Location.id, Hostel.name, Floor.floor_number, Wing.wing_name, Location.area_type, func.count(Issue.id))
                   .join(Wing, Location.wing_id == Wing.id).join(Floor, Wing.floor_id == Floor.id).join(Hostel, Floor.hostel_id == Hostel.id)
                   .join(Issue, Issue.location_id == Location.id, isouter=True)
                   .group_by(Location.id, Hostel.name, Floor.floor_number, Wing.wing_name, Location.area_type).order_by(func.count(Issue.id).desc()).limit(10).all())
    by_problem = (db.query(ProblemType.name, func.count(Issue.id)).join(Issue, Issue.problem_type_id == ProblemType.id, isouter=True)
                  .group_by(ProblemType.name).order_by(func.count(Issue.id).desc()).limit(10).all())
    overdue = db.query(Issue).filter(Issue.due_date.is_not(None), Issue.due_date < datetime.utcnow().date(), Issue.status.notin_(["closed", "rejected"])).count()
    reopened = db.query(Issue).filter(Issue.status == "reopened").count()
    resolved_count = db.query(Issue).filter(Issue.resolved_at.is_not(None)).count()
    avg_resolution_hours = None
    if resolved_count:
        durations = db.query(Issue.created_at, Issue.resolved_at).filter(Issue.resolved_at.is_not(None)).all()
        seconds = [(resolved - created).total_seconds() for created, resolved in durations if resolved and created]
        avg_resolution_hours = round(sum(seconds) / len(seconds) / 3600, 2) if seconds else None
    return {"total_issues": db.query(Issue).count(),
            "by_status": [{"status":s,"count":n} for s,n in by_status],
            "by_category": [{"category":s,"count":n} for s,n in by_category],
            "by_location": [{"location_id":i,"location":f"{h} · Floor {f} · Wing {w} · {a}","count":n} for i,h,f,w,a,n in by_location],
            "by_problem_type": [{"problem_type":s,"count":n} for s,n in by_problem],
            "overdue_count": overdue, "reopened_count": reopened, "average_resolution_hours": avg_resolution_hours}

@router.post("/admin/hostels", status_code=201)
def create_hostel(payload: HostelCreate, actor: User = Depends(require_role("administrator")), db: Session = Depends(get_db)):
    if db.query(Hostel).filter(func.lower(Hostel.name) == payload.name.strip().lower()).first(): raise HTTPException(409, "Hostel already exists")
    row=Hostel(name=payload.name.strip()); db.add(row); db.commit(); db.refresh(row); return row

@router.post("/admin/floors", status_code=201)
def create_floor(payload: FloorCreate, actor: User = Depends(require_role("administrator")), db: Session = Depends(get_db)):
    if not db.get(Hostel,payload.hostel_id): raise HTTPException(404,"Hostel not found")
    if db.query(Floor).filter_by(hostel_id=payload.hostel_id,floor_number=payload.floor_number).first(): raise HTTPException(409,"Floor already exists")
    row=Floor(**payload.model_dump()); db.add(row); db.commit(); db.refresh(row); return row

@router.post("/admin/wings", status_code=201)
def create_wing(payload: WingCreate, actor: User = Depends(require_role("administrator")), db: Session = Depends(get_db)):
    if not db.get(Floor,payload.floor_id): raise HTTPException(404,"Floor not found")
    name=payload.wing_name.strip().upper()
    if db.query(Wing).filter_by(floor_id=payload.floor_id,wing_name=name).first(): raise HTTPException(409,"Wing already exists")
    row=Wing(floor_id=payload.floor_id,wing_name=name); db.add(row); db.commit(); db.refresh(row); return row

@router.post("/admin/locations", status_code=201)
def create_location(payload: LocationCreate, actor: User = Depends(require_role("administrator")), db: Session = Depends(get_db)):
    if not db.get(Wing,payload.wing_id): raise HTTPException(404,"Wing not found")
    if db.query(Location).filter_by(wing_id=payload.wing_id,area_type=payload.area_type.strip()).first(): raise HTTPException(409,"Location already exists in this wing")
    row=Location(wing_id=payload.wing_id,area_type=payload.area_type.strip(),description=payload.description); db.add(row); db.commit(); db.refresh(row); return row

@router.patch("/admin/locations/{location_id}")
def patch_location(location_id:int,payload:LocationPatch,actor:User=Depends(require_role("administrator")),db:Session=Depends(get_db)):
    row=db.get(Location,location_id)
    if not row: raise HTTPException(404,"Location not found")
    for k,v in payload.model_dump(exclude_unset=True).items(): setattr(row,k,v.strip() if isinstance(v,str) else v)
    db.commit(); db.refresh(row); return row

@router.post("/admin/categories", status_code=201)
def create_category(payload: CategoryCreate, actor: User = Depends(require_role("administrator")), db: Session = Depends(get_db)):
    if db.query(Category).filter(func.lower(Category.name)==payload.name.strip().lower()).first(): raise HTTPException(409,"Category already exists")
    row=Category(name=payload.name.strip(),description=payload.description,resolution_target_hours=payload.resolution_target_hours); db.add(row); db.commit(); db.refresh(row); return row

@router.patch("/admin/categories/{category_id}")
def patch_category(category_id:int,payload:CategoryPatch,actor:User=Depends(require_role("administrator")),db:Session=Depends(get_db)):
    row=db.get(Category,category_id)
    if not row: raise HTTPException(404,"Category not found")
    for k,v in payload.model_dump(exclude_unset=True).items(): setattr(row,k,v)
    db.commit(); db.refresh(row); return row

@router.post("/admin/problem-types", status_code=201)
def create_problem_type(payload: ProblemTypeCreate, actor: User = Depends(require_role("administrator")), db: Session = Depends(get_db)):
    if not db.get(Category,payload.category_id): raise HTTPException(404,"Category not found")
    if db.query(ProblemType).filter_by(category_id=payload.category_id,name=payload.name.strip()).first(): raise HTTPException(409,"Problem type already exists")
    row=ProblemType(category_id=payload.category_id,name=payload.name.strip(),description=payload.description,requires_description=payload.requires_description); db.add(row); db.commit(); db.refresh(row); return row

@router.patch("/admin/problem-types/{problem_type_id}")
def patch_problem_type(problem_type_id:int,payload:ProblemTypePatch,actor:User=Depends(require_role("administrator")),db:Session=Depends(get_db)):
    row=db.get(ProblemType,problem_type_id)
    if not row: raise HTTPException(404,"Problem type not found")
    for k,v in payload.model_dump(exclude_unset=True).items(): setattr(row,k,v.strip() if isinstance(v,str) else v)
    db.commit(); db.refresh(row); return row

@router.post("/admin/assets", status_code=201)
def create_asset(payload: AssetCreate, actor: User = Depends(require_role("administrator")), db: Session = Depends(get_db)):
    if not db.get(Hostel,payload.hostel_id): raise HTTPException(404,"Hostel not found")
    row=Asset(hostel_id=payload.hostel_id,name=payload.name.strip(),asset_type=payload.asset_type.strip(),description=payload.description); db.add(row); db.flush()
    for lid in set(payload.location_ids):
        if not db.get(Location,lid): raise HTTPException(422,f"Unknown location_id: {lid}")
        db.add(AssetLocation(asset_id=row.id,location_id=lid))
    db.commit(); db.refresh(row); return row

@router.patch("/admin/assets/{asset_id}")
def patch_asset(asset_id:int,payload:AssetPatch,actor:User=Depends(require_role("administrator")),db:Session=Depends(get_db)):
    row=db.get(Asset,asset_id)
    if not row: raise HTTPException(404,"Asset not found")
    for k,v in payload.model_dump(exclude_unset=True).items(): setattr(row,k,v.strip() if isinstance(v,str) else v)
    db.commit(); db.refresh(row); return row

@router.post("/admin/assets/{asset_id}/locations", status_code=201)
def link_asset_location(asset_id:int,payload:AssetLocationLink,actor:User=Depends(require_role("administrator")),db:Session=Depends(get_db)):
    if not db.get(Asset,asset_id): raise HTTPException(404,"Asset not found")
    if not db.get(Location,payload.location_id): raise HTTPException(404,"Location not found")
    if db.query(AssetLocation).filter_by(asset_id=asset_id,location_id=payload.location_id).first(): raise HTTPException(409,"Asset is already linked to this location")
    row=AssetLocation(asset_id=asset_id,location_id=payload.location_id); db.add(row); db.commit(); return {"asset_id":asset_id,"location_id":payload.location_id}

@router.delete("/admin/assets/{asset_id}/locations/{location_id}", status_code=204)
def unlink_asset_location(asset_id:int,location_id:int,actor:User=Depends(require_role("administrator")),db:Session=Depends(get_db)):
    row=db.query(AssetLocation).filter_by(asset_id=asset_id,location_id=location_id).first()
    if not row: raise HTTPException(404,"Asset-location link not found")
    db.delete(row); db.commit()
