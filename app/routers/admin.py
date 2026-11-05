from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.db.session import get_db
from app.models import Issue, Category, ProblemType, User
from app.routers.deps import require_role
router = APIRouter(tags=["Admin"])

class StaffCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=255)
    category_id: int = Field(gt=0)

@router.post("/admin/staff", status_code=201)
def create_staff(payload: StaffCreate, actor: User = Depends(require_role("administrator")), db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if db.query(User).filter(func.lower(User.email) == email).first():
        raise HTTPException(409, "An account with this email already exists")
    category = db.get(Category, payload.category_id)
    if not category:
        raise HTTPException(422, "Unknown category_id")
    user = User(name=payload.name.strip(), email=email, role="staff", category_id=category.id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "category_id": user.category_id}

@router.get("/admin/analytics")
def analytics(actor: User = Depends(require_role("administrator")), db: Session = Depends(get_db)):
    by_status = db.query(Issue.status, func.count(Issue.id)).group_by(Issue.status).all()
    by_category = (db.query(Category.name, func.count(Issue.id))
                   .join(ProblemType, ProblemType.category_id == Category.id)
                   .join(Issue, Issue.problem_type_id == ProblemType.id, isouter=True)
                   .group_by(Category.name).all())
    return {"total_issues": db.query(Issue).count(),
            "by_status": [{"status":s,"count":n} for s,n in by_status],
            "by_category": [{"category":s,"count":n} for s,n in by_category]}
