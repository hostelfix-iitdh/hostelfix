from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Issue, Category, ProblemType, User
from app.routers.deps import require_role
router = APIRouter(tags=["Admin"])
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
